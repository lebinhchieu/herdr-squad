# Scenario for tests/test_ca_win.py: dot-sources claude-accounts.ps1 once per case and prints one JSON line per
# case: {"name":..., "ok":true|false, "detail":...}. ASCII only. Case names are "<bash class>.<bash test>"
# where tests/test_ca_launchers.py has the twin, and "ps.<name>" for the PowerShell-only ones.
#
# Isolation (the runner sets it): USERPROFILE points at a temp dir on the WSL side, so $HOME is not the PO's.
# Every case gets its own CLAUDE_ACCOUNTS_HOME under $Tmp. Herdr is a mock (Invoke-ClaudeHerdr redefined),
# `claude` and the Git-bash relink are functions; only the "ps.Invoke-ClaudeHerdr" cases use the real function,
# against cmd.exe, never the real herdr.
param([string]$Ps1, [string]$Tmp, [string]$Fix, [string]$HomeDir)
$ErrorActionPreference = 'Continue'

# Guard (P10), before anything is dot-sourced: the run may only touch a temp dir on the WSL side (or the OS temp
# dir), never a Windows disk path under a user profile, and $HOME must be the test's own.
function Test-SafeDir([string]$p) {
    if (-not $p -or -not $p.Trim()) { return $false }
    if ($p -match '^[A-Za-z]:\\Users\\' -and $p -notmatch '\\AppData\\Local\\Temp\\') { return $false }
    if ($p -match '^[A-Za-z]:\\?$') { return $false }
    $true
}
foreach ($d in $Tmp, $HomeDir) { if (-not (Test-SafeDir $d)) { throw "unsafe or empty test dir: <$d>" } }
if ($env:USERPROFILE -ne $HomeDir -or $HOME -ne $HomeDir) { throw "HOME <$HOME> / USERPROFILE <$env:USERPROFILE> is not the test home <$HomeDir>" }
$script:N = 0

function Say($name, $ok, $detail) {
    [Console]::Out.WriteLine((@{ name = $name; ok = [bool]$ok; detail = "$detail" } | ConvertTo-Json -Compress))
}
function Check($cond, $msg) { if (-not $cond) { throw $msg } }
function Eq($got, $want, $what) {
    if (-not ($got -ceq $want) -or ($null -eq $got) -ne ($null -eq $want)) {
        throw "$what : got <$(Show $got)> want <$(Show $want)>"
    }
}
function Show($v) {
    if ($null -eq $v) { return '$null' }
    "$(if ($v -is [array]) { '@(' + (($v | ForEach-Object { Show $_ }) -join ',') + ')' } else { "$v" } )".Replace("`n", '\n').Replace("`r", '\r')
}
function Bytes($path) { if (Test-Path -LiteralPath $path) { ,[IO.File]::ReadAllBytes($path) } else { $null } }
function FileText($path) {
    $b = Bytes $path
    if ($null -eq $b) { return $null }
    [Text.Encoding]::ASCII.GetString($b)
}

# Run a script block, return @{ Out = success-stream items; Msg = text of every other stream, joined by \n }.
function Cap([scriptblock]$sb) {
    $out = New-Object System.Collections.ArrayList
    $msg = New-Object System.Collections.ArrayList
    foreach ($i in (& $sb *>&1)) {
        if ($i -is [System.Management.Automation.ErrorRecord]) { [void]$msg.Add($i.Exception.Message) }
        elseif ($i -is [System.Management.Automation.InformationRecord]) { [void]$msg.Add("$($i.MessageData)") }
        elseif ($i -is [System.Management.Automation.WarningRecord] -or $i -is [System.Management.Automation.VerboseRecord]) { [void]$msg.Add("$($i.Message)") }
        elseif ($null -ne $i) { [void]$out.Add($i) }   # a function's `return $null` is failure, not an output
    }
    @{ Out = @($out); Msg = ($msg -join "`n") }
}

# workspace list JSON built from rows (id, number, label), shaped like the real sample.
function WsJson($rows) {
    $ws = @(foreach ($r in $rows) {
        [ordered]@{ active_tab_id = "$($r[0]):t1"; agent_status = 'idle'; focused = $false; label = $r[2]; number = $r[1]
                    pane_count = 1; tab_count = 1; workspace_id = $r[0] }
    })
    (@{ id = 'cli:workspace:list'; result = @{ type = 'workspace_list'; workspaces = $ws } } | ConvertTo-Json -Compress -Depth 6)
}
function RealJson($name) { (Get-Content -LiteralPath (Join-Path $Fix $name) -Raw).Trim() }

# Mock herdr (defined per case, after the dot-source): logs every call, `workspace list` answers $script:WsList
# ($null = herdr failed), anything else ''.
function Reports { @($script:HerdrLog | Where-Object { $_.Args[1] -eq 'report-metadata' }) }

$script:Claude = New-Object System.Collections.ArrayList
$script:BashCalls = New-Object System.Collections.ArrayList
function claude {
    $script:Claude.Add(@{ Cfg = $env:CLAUDE_CONFIG_DIR; Args = @($args) }) | Out-Null
}
function ca-stub-bash { $script:BashCalls.Add(@($args)) | Out-Null }

$script:ClearEnv = 'HERDR_ENV', 'HERDR_WORKSPACE_ID', 'ACCT_NO_WS_DEFAULT', 'CLAUDE_CONFIG_DIR', 'CLAUDE_ACCOUNTS_HOME'
function Case([string]$name, [scriptblock]$body, [switch]$RealHerdr) {
    $script:N++
    $home_ = Join-Path $Tmp "h$($script:N)"
    New-Item -ItemType Directory -Force -Path $home_ | Out-Null
    foreach ($v in $script:ClearEnv) { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
    $env:CLAUDE_ACCOUNTS_HOME = $home_
    $script:AcctDir = $home_
    $script:WsDir = Join-Path $home_ 'workspace-default'
    $script:HerdrLog = New-Object System.Collections.ArrayList
    $script:Claude.Clear(); $script:BashCalls.Clear()
    $script:WsList = RealJson 'workspace-list.real.json'
    try {
        . $Ps1
        if (-not $RealHerdr) {
            # redefine after the dot-source: the mock shadows the real function in this scope
            function Invoke-ClaudeHerdr {
                $a = @($args)
                $script:HerdrLog.Add(@{ Args = @($a[0]); Timeout = $a[1] }) | Out-Null
                if (@($a[0])[0] -eq 'workspace' -and @($a[0])[1] -eq 'list') { return $script:WsList }
                return ''
            }
        }
        $script:GitBash = 'ca-stub-bash'
        $script:HerdrLog.Clear(); $script:Claude.Clear(); $script:BashCalls.Clear()
        . $body
        Say $name $true ''
    } catch {
        Say $name $false ("$($_.Exception.Message) @ line $($_.InvocationInfo.ScriptLineNumber)")
    } finally {
        foreach ($v in $script:ClearEnv) { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
    }
}
function WsFile($name, $text) {
    New-Item -ItemType Directory -Force -Path $script:WsDir | Out-Null
    [IO.File]::WriteAllText((Join-Path $script:WsDir $name), $text)
}
function GlobalFile($text) { [IO.File]::WriteAllText((Join-Path $script:AcctDir 'default'), $text) }
function InHerdr($id = 'w26') { $env:HERDR_ENV = '1'; $env:HERDR_WORKSPACE_ID = $id }
function SetWs($rows) { $script:WsList = WsJson $rows }
function NoWsDir { Check (-not (Test-Path -LiteralPath $script:WsDir)) 'workspace-default was created' }
$USAGE = 'usage: cdefault --ws [<workspace id|panel number|label>] <1|2|3>'
function CfgOf($n) { if ($n -eq 1) { $null } else { Join-Path $HOME $(if ($n -eq 2) { '.claude-b' } else { '.claude-3' }) } }

# ---------------------------------------------------------------- contract: names, home, ids
Case 'ps.AcctHome_is_the_override_and_ps1_is_ascii' {
    Eq $script:AcctHome $script:AcctDir 'AcctHome'
    Check ((Bytes $Ps1 | Where-Object { $_ -gt 127 }).Count -eq 0) 'claude-accounts.ps1 has a non-ASCII byte'
    foreach ($f in 'Test-WsId', 'Invoke-ClaudeHerdr', 'Get-ClaudeGlobalDefault', 'Get-ClaudeDefaultAccount', 'Resolve-ClaudeWorkspace',
                   'Send-ClaudeWorkspaceAccount', 'Set-ClaudeWorkspaceDefault', 'c1', 'c2', 'c3', 'c', 'cdefault') {
        Check (Get-Command $f -CommandType Function -ErrorAction SilentlyContinue) "function $f is not defined"
    }
}

Case 'ps.AcctHome_default_is_HOME_claude-accounts' {
    Remove-Item Env:CLAUDE_ACCOUNTS_HOME -ErrorAction SilentlyContinue
    . $Ps1
    Eq $script:AcctHome (Join-Path $HOME '.claude-accounts') 'AcctHome default'
    Eq "$HOME" $HomeDir 'HOME'
    Check ("$HOME" -notmatch '84084') 'HOME is the PO profile'
}

Case 'WsIdOkTest.test_accepts_and_rejects' {
    foreach ($g in 'w1', 'w2F', 'wA', 'w26') { Check (Test-WsId $g) "good id refused: $g" }
    foreach ($b in '', 'w', 'x1', 'w/../x', 'w 1', "w1`n", "w1`r`n", 'w1;rm', 'W1', 'w-1', 'w1.', "`nw1", ' w1') {
        Check (-not (Test-WsId $b)) "bad id accepted: <$(Show $b)>"
    }
    Check (-not (Test-WsId $null)) 'null id accepted'
}
Case 'ps.Test-WsId_trailing_newline_and_upper_W' {
    Check (-not (Test-WsId "w1`n")) '"w1`n" is an id (needs \z, not $)'
    Check (-not (Test-WsId 'W1')) 'W1 is an id (needs -cmatch)'
    Check (Test-WsId 'w2H') 'w2H is not an id'
}

# ---------------------------------------------------------------- global default, default_account
Case 'DefaultAccountTest.test_global_default_valid_values_and_fallback' {
    Eq (Get-ClaudeGlobalDefault) '1' 'no file'
    foreach ($p in @(('1', '1'), ("1`n", '1'), ("2`n", '2'), ('3', '3'), ('', '1'), ('4', '1'), ('0', '1'), ('abc', '1'),
                     ('12', '1'), ('2x', '1'), ("2`r`n", '2'), ("`r`n", '1'))) {
        GlobalFile $p[0]
        $got = Get-ClaudeGlobalDefault
        Check ($got -is [string]) "not a string for <$(Show $p[0])>: $($got.GetType().Name)"
        Eq $got $p[1] "global default of <$(Show $p[0])>"
    }
}
Case 'ps.global_default_empty_file_and_crlf_and_held_open' {
    GlobalFile ''
    Eq (Get-ClaudeGlobalDefault) '1' 'empty default file'
    GlobalFile "3`r`n"
    Eq (Get-ClaudeGlobalDefault) '3' 'default with CRLF'
    $fs = [IO.File]::Open((Join-Path $script:AcctDir 'default'), 'Open', 'ReadWrite', 'ReadWrite, Delete')
    try { Eq (Get-ClaudeGlobalDefault) '3' 'read while another handle is open (ReadWrite, Delete)' } finally { $fs.Dispose() }
}
Case 'DefaultAccountTest.test_workspace_file_beats_global_inside_herdr' {
    GlobalFile '2'
    InHerdr
    foreach ($v in '1', '2', '3') { WsFile 'w26' "$v`n"; Eq (Get-ClaudeDefaultAccount) $v "ws file $v" }
}
Case 'DefaultAccountTest.test_workspace_file_ignored_outside_herdr_or_with_a_bad_id' {
    GlobalFile '2'; WsFile 'w26' '3'
    $env:HERDR_WORKSPACE_ID = 'w26'
    Eq (Get-ClaudeDefaultAccount) '2' 'no HERDR_ENV'
    $env:HERDR_ENV = '0'
    Eq (Get-ClaudeDefaultAccount) '2' 'HERDR_ENV=0'
    Remove-Item Env:HERDR_WORKSPACE_ID; $env:HERDR_ENV = '1'
    Eq (Get-ClaudeDefaultAccount) '2' 'no id'
    foreach ($bad in '../x', 'x26', 'w 26', "w26`n", 'W26') {
        $env:HERDR_WORKSPACE_ID = $bad
        Eq (Get-ClaudeDefaultAccount) '2' "bad id <$(Show $bad)>"
    }
}
Case 'DefaultAccountTest.test_garbage_workspace_file_falls_to_global_and_then_1' {
    InHerdr
    foreach ($v in '0', '4', '9', '', 'abc', '22', 'x', "`r`n") {
        WsFile 'w26' $v
        Eq (Get-ClaudeDefaultAccount) '1' "no global, ws <$(Show $v)>"
        GlobalFile '3'
        Eq (Get-ClaudeDefaultAccount) '3' "global 3, ws <$(Show $v)>"
        Remove-Item (Join-Path $script:AcctDir 'default')
    }
}
Case 'ps.workspace_file_with_crlf_and_read_while_held_open' {
    InHerdr
    WsFile 'w26' "2`r`n"
    Eq (Get-ClaudeDefaultAccount) '2' 'ws file with CRLF'
    $fs = [IO.File]::Open((Join-Path $script:WsDir 'w26'), 'Open', 'ReadWrite', 'ReadWrite, Delete')
    try { Eq (Get-ClaudeDefaultAccount) '2' 'read while another handle is open' } finally { $fs.Dispose() }
}

# ---------------------------------------------------------------- resolve_workspace
function Resolve($ref) { Cap { Resolve-ClaudeWorkspace $ref } }
function ResolvesTo($ref, $want) {
    $r = Resolve $ref
    Eq $r.Out.Count 1 "outputs for <$(Show $ref)>"
    Eq $r.Out[0] $want "resolve <$(Show $ref)>"
    Eq $r.Msg '' "messages for <$(Show $ref)>"
}
function Refused($ref, $msgPart) {
    $r = Resolve $ref
    Eq $r.Out.Count 0 "outputs for <$(Show $ref)>"
    Check ($r.Msg -like "*$msgPart*") "message for <$(Show $ref)> was <$(Show $r.Msg)>, want <$msgPart>"
    $r
}
Case 'ResolveWorkspaceTest.test_real_sample_by_id_number_and_label' {
    foreach ($ref in 'w26', '1', 'claude-accounts') { ResolvesTo $ref 'w26' }
    $script:WsList = RealJson 'workspace-list-windows.real.json'
    foreach ($ref in 'w6', '1', 'enemy-spritesheet') { ResolvesTo $ref 'w6' }
    $script:WsList = RealJson 'workspace-list-3.real.json'
    foreach ($p in @(('w26', 'w26'), ('w2H', 'w2H'), ('2', 'w2H'), ('squad', 'w2H'), ('3', 'w2J'), ('wpw', 'w2J'), ('w2J', 'w2J'), ('1', 'w26'))) {
        ResolvesTo $p[0] $p[1]
    }
    Check ($script:HerdrLog[0].Args -join ' ' -ceq 'workspace list') 'first herdr call was not workspace list'
    Eq $script:HerdrLog[0].Timeout 5 'workspace list timeout'
}
Case 'ResolveWorkspaceTest.test_each_tier_in_a_list_with_several_workspaces' {
    SetWs @(@('wA1', 1, 'alpha'), @('wB2', 2, 'beta'), @('wC3', 3, 'beta2'))
    foreach ($p in @(('wB2', 'wB2'), ('3', 'wC3'), ('alpha', 'wA1'), ('beta2', 'wC3'))) { ResolvesTo $p[0] $p[1] }
}
Case 'ResolveWorkspaceTest.test_tier_order_id_then_number_then_label' {
    SetWs @(@('w7', 1, 'x'), @('wC', 7, 'w7'))
    ResolvesTo 'w7' 'w7'
    SetWs @(@('wA', 1, '2'), @('wB', 2, 'other'))
    ResolvesTo '2' 'wB'
    SetWs @(@('wA', 1, '2'), @('wB', 5, 'other'))
    ResolvesTo '2' 'wA'
}
Case 'ResolveWorkspaceTest.test_number_tier_is_digits_only' {
    SetWs @(, @('wA', 1, 'one'))
    foreach ($ref in '01', '+1', '1.0', ' 1', "1`n", [string][char]0x0661) { $null = Refused $ref 'no workspace matches' }
}
Case 'ps.Resolve-ClaudeWorkspace_is_case_sensitive' {
    $script:WsList = RealJson 'workspace-list-3.real.json'
    $r = Resolve 'w2h'; Eq $r.Out[0] 'w2h' 'w2h is not w2H: it is a raw id-shaped ref'
    $null = Refused 'SQUAD' 'no workspace matches SQUAD'
    $null = Refused 'W2H' 'no workspace matches W2H'
    SetWs @(@('wA1', 1, 'Beta'))
    $null = Refused 'beta' 'no workspace matches beta'
}
Case 'ResolveWorkspaceTest.test_ambiguous_in_the_winning_tier_lists_candidates' {
    foreach ($t in @(@(@(@('wA1', 1, 'dup'), @('wB2', 2, 'dup')), 'dup'), @(@(@('wA1', 4, 'x'), @('wB2', 4, 'y')), '4'))) {
        SetWs $t[0]
        $r = Refused $t[1] "ambiguous: $($t[1]) matches"
        Check ($r.Msg.StartsWith("ambiguous: $($t[1]) matches")) "message does not start with ambiguous: <$(Show $r.Msg)>"
        foreach ($row in $t[0]) { Check ($r.Msg -like "*$($row[0]) (panel $($row[1])) $($row[2])*") "candidate line for $($row[0]) missing: <$(Show $r.Msg)>" }
    }
}
Case 'ResolveWorkspaceTest.test_no_hit_idshaped_is_a_raw_id_otherwise_error' {
    ResolvesTo 'wZ9' 'wZ9'
    $null = Refused 'nothing here' 'no workspace matches nothing here'
    $null = Refused '99' 'no workspace matches 99'
}
Case 'ResolveWorkspaceTest.test_blank_ref_is_an_error' {
    foreach ($ref in '', '   ', "`t") { $null = Refused $ref 'no workspace matches' }
}
Case 'ResolveWorkspaceTest.test_herdr_failure_or_bad_json_use_the_raw_id_rule' {
    foreach ($bad in $null, 'not json {', '{"id":"x","result":{}}', '[]', '{"result":{"workspaces":[]}}', '{"result":{"workspaces":null}}') {
        $script:WsList = $bad
        ResolvesTo 'wQ1' 'wQ1'
        $null = Refused 'claude-accounts' 'no workspace matches claude-accounts'
        $null = Refused '1' 'no workspace matches 1'
    }
}
Case 'ResolveWorkspaceTest.test_a_listed_id_that_is_not_id_shaped_is_not_returned' {
    SetWs @(, @('bad/id', 1, 'alpha'))
    $null = Refused 'alpha' 'no workspace matches alpha'
    $null = Refused '1' 'no workspace matches 1'
    # one hit with a bad id ends the tiers (as bash): the raw-id rule decides, not the next tier
    SetWs @(@('bad/id', 1, 'x'), @('wOk', 2, '1'))
    $null = Refused '1' 'no workspace matches 1'
    SetWs @(, @('bad/id', 1, 'wQ9'))
    ResolvesTo 'wQ9' 'wQ9'
}

# ---------------------------------------------------------------- Send-ClaudeWorkspaceAccount, set_workspace_default
Case 'ps.Send-ClaudeWorkspaceAccount_args_timeout_and_silence' {
    $r = Cap { Send-ClaudeWorkspaceAccount 'w26' '3' }
    Eq $r.Out.Count 0 'output'; Eq $r.Msg '' 'messages'
    Eq @(Reports).Count 1 'report calls'
    $c = @(Reports)[0]
    Eq ($c.Args[0..6] -join ' ') 'workspace report-metadata w26 --source claude-accounts --token account=c3' 'argv'
    Eq $c.Args[7] '--seq' 'seq flag'
    Check ("$($c.Args[8])" -cmatch '^\d{13}$') "seq is not 13 digits: $($c.Args[8])"
    Check ([math]::Abs([long]$c.Args[8] - [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -lt 60000) 'seq is not epoch ms'
    Eq $c.Timeout 3 'timeout'
}
Case 'SetWorkspaceDefaultTest.test_bad_account_is_false_and_no_file' {
    foreach ($a in '4', '0', 'x', '', '12', 'c1') {
        $r = Set-ClaudeWorkspaceDefault $a 'w26'
        Check ($r -is [bool] -and -not $r) "account <$a> returned <$(Show $r)>"
    }
    NoWsDir
}
Case 'SetWorkspaceDefaultTest.test_outside_herdr_without_id_is_a_noop' {
    $env:HERDR_WORKSPACE_ID = 'w26'
    $r = Set-ClaudeWorkspaceDefault '2'
    Check ($r -is [bool] -and $r) "returned <$(Show $r)>"
    NoWsDir
    Eq $script:HerdrLog.Count 0 'herdr calls'
}
Case 'SetWorkspaceDefaultTest.test_env_id_inside_herdr_and_report_metadata_once' {
    InHerdr
    $r = Cap { Set-ClaudeWorkspaceDefault '2' }
    Eq $r.Out.Count 1 'outputs'; Check ($r.Out[0] -is [bool] -and $r.Out[0]) 'not $true'; Eq $r.Msg '' 'messages'
    $b = Bytes (Join-Path $script:WsDir 'w26')
    Eq ($b -join ',') '50,10' 'file bytes ("2" LF, no BOM)'
    Eq @(Reports).Count 1 'report calls'
    $c = @(Reports)[0]
    Eq ($c.Args[0..6] -join ' ') 'workspace report-metadata w26 --source claude-accounts --token account=c2' 'argv'
    Check ("$($c.Args[8])" -cmatch '^\d{13}$') 'seq'
    Eq $c.Timeout 3 'report timeout'
    $list = @($script:HerdrLog | Where-Object { $_.Args[1] -eq 'list' })
    Eq $list.Count 1 'list calls'; Eq $list[0].Timeout 5 'list timeout'
}
Case 'SetWorkspaceDefaultTest.test_seq_is_epoch_ms_and_increases' {
    1..3 | ForEach-Object { $null = Set-ClaudeWorkspaceDefault '1' 'w26'; Start-Sleep -Milliseconds 10 }
    $s = @(Reports | ForEach-Object { [long]$_.Args[8] })
    Eq $s.Count 3 'report calls'
    Check ($s[0] -lt $s[1] -and $s[1] -lt $s[2]) "seqs do not increase: $($s -join ',')"
}
Case 'SetWorkspaceDefaultTest.test_explicit_id_works_outside_herdr_and_overwrites' {
    SetWs @(, @('wB2', 2, 'b'))
    Check (Set-ClaudeWorkspaceDefault '3' 'wB2') 'first write failed'
    Eq (FileText (Join-Path $script:WsDir 'wB2')) "3`n" 'content'
    Check (Set-ClaudeWorkspaceDefault '1' 'wB2') 'overwrite failed'
    Eq (FileText (Join-Path $script:WsDir 'wB2')) "1`n" 'content after overwrite'
    Eq (@(Get-ChildItem -Force $script:WsDir).Name -join ',') 'wB2' 'files left (no .tmp.*)'
}
Case 'SetWorkspaceDefaultTest.test_bad_id_is_true_and_writes_nothing' {
    foreach ($bad in '../evil', 'x1', 'w/1', 'w 1', 'w', "w1`n", 'W1') {
        $r = Set-ClaudeWorkspaceDefault '1' $bad
        Check ($r -is [bool] -and $r) "id <$(Show $bad)> returned <$(Show $r)>"
    }
    NoWsDir
    $env:HERDR_ENV = '1'; $env:HERDR_WORKSPACE_ID = '../x'
    Check (Set-ClaudeWorkspaceDefault '1') 'env bad id returned false'
    NoWsDir
    Eq @(Reports).Count 0 'report calls'
}
Case 'SetWorkspaceDefaultTest.test_parallel_writers_all_land_here_in_sequence' {
    # a real parallel run on NTFS is on the PO checklist (a UNC share cannot rename over an open file)
    $ids = 1..8 | ForEach-Object { "w$_" }
    SetWs @(for ($n = 1; $n -le 8; $n++) { , @("w$n", $n, "l$n") })
    for ($n = 0; $n -lt 8; $n++) { Check (Set-ClaudeWorkspaceDefault "$($n % 3 + 1)" $ids[$n]) "writer $n" }
    Eq ((@(Get-ChildItem -Force $script:WsDir).Name | Sort-Object) -join ',') (($ids | Sort-Object) -join ',') 'files'
    for ($n = 0; $n -lt 8; $n++) { Eq (FileText (Join-Path $script:WsDir $ids[$n])) "$($n % 3 + 1)`n" $ids[$n] }
}
Case 'SetWorkspaceDefaultTest.test_prune_removes_unlisted_and_keeps_listed_current_and_non_id_files' {
    foreach ($n in 'wGone', 'wKeep', 'wCur', 'w.x', 'w-1', 'notws', '.tmp.stale', '.tmp.wGone', 'W1') { WsFile $n "2`n" }
    SetWs @(@('wKeep', 1, 'k'), @('wOther', 2, 'o'))   # the current id is not even listed
    $null = Set-ClaudeWorkspaceDefault '1' 'wCur'
    Eq ((@(Get-ChildItem -Force $script:WsDir).Name | Sort-Object) -join ',') (('.tmp.stale', '.tmp.wGone', 'W1', 'notws', 'w-1', 'w.x', 'wCur', 'wKeep' | Sort-Object) -join ',') 'files after prune'
}
Case 'ps.a_stale_tmp_file_is_never_pruned' {
    WsFile '.tmp.abc123' "9`n"
    SetWs @(, @('wA', 1, 'a'))
    $null = Set-ClaudeWorkspaceDefault '2' 'wB'
    Check (Test-Path -LiteralPath (Join-Path $script:WsDir '.tmp.abc123')) 'stale .tmp.* file was deleted'
}
Case 'SetWorkspaceDefaultTest.test_no_prune_when_list_fails_is_empty_or_bad' {
    WsFile 'wOld' "2`n"
    foreach ($bad in $null, '{bad', (WsJson @())) {
        $script:WsList = $bad
        Check (Set-ClaudeWorkspaceDefault '1' 'wA') "write failed for list <$(Show $bad)>"
        Check (Test-Path -LiteralPath (Join-Path $script:WsDir 'wOld')) "wOld pruned for list <$(Show $bad)>"
    }
    Eq (FileText (Join-Path $script:WsDir 'wA')) "1`n" 'wA content'
}
Case 'SetWorkspaceDefaultTest.test_unwritable_workspace_default_is_false' {
    [IO.File]::WriteAllText($script:WsDir, 'a file, not a dir')
    $r = Cap { Set-ClaudeWorkspaceDefault '2' 'w26' }
    Check ($r.Out.Count -eq 1 -and $r.Out[0] -is [bool] -and -not $r.Out[0]) "returned <$(Show $r.Out)>"
    Eq @(Reports).Count 0 'report calls'
}
Case 'SetWorkspaceDefaultTest.test_move_failure_after_tmp_is_false_leaves_no_tmp_and_does_not_report' {
    # the destination is a non-empty directory: the rename onto it fails, as bash's mv -f into an unwritable one
    New-Item -ItemType Directory -Force -Path (Join-Path $script:WsDir 'w26') | Out-Null
    [IO.File]::WriteAllText((Join-Path $script:WsDir 'w26\keep'), 'x')
    $r = Cap { Set-ClaudeWorkspaceDefault '2' 'w26' }
    Check ($r.Out.Count -eq 1 -and $r.Out[0] -is [bool] -and -not $r.Out[0]) "returned <$(Show $r.Out)>"
    Eq @(Get-ChildItem -Force -Filter '.tmp.*' $script:WsDir).Count 0 'tmp files left'
    Eq @(Reports).Count 0 'report calls'
}
Case 'ps.destination_held_open_is_recorded_not_asserted' {
    # NTFS: a reader opened with FileShare ReadWrite,Delete never blocks the rename. A UNC share may refuse
    # (probed: "Access to the path is denied"). So: only "no throw, a bool, no .tmp left" is required.
    WsFile 'w26' "1`n"
    $fs = [IO.File]::Open((Join-Path $script:WsDir 'w26'), 'Open', 'Read', 'ReadWrite, Delete')
    $t = Get-Date
    try { $r = Cap { Set-ClaudeWorkspaceDefault '3' 'w26' } } finally { $fs.Dispose() }
    $sec = ((Get-Date) - $t).TotalSeconds
    Check ($r.Out.Count -eq 1 -and $r.Out[0] -is [bool]) "no bool: <$(Show $r.Out)>"
    Check ($sec -lt 5) "took $sec s"
    Eq @(Get-ChildItem -Force -Filter '.tmp.*' $script:WsDir).Count 0 'tmp files left'
    $script:Note = "returned $($r.Out[0]); content now <$(Show (FileText (Join-Path $script:WsDir 'w26')))>; $([math]::Round($sec,2)) s"
    [Console]::Out.WriteLine((@{ name = 'note.destination_held_open'; ok = $true; detail = $script:Note } | ConvertTo-Json -Compress))
}

# ---------------------------------------------------------------- launchers
function Last { Check ($script:Claude.Count -eq 1) "claude calls: $($script:Claude.Count)"; $script:Claude[0] }
Case 'LaunchersTest.test_c1_unsets_config_dir_even_if_the_parent_exports_it' {
    $env:CLAUDE_CONFIG_DIR = '/should/vanish'
    $r = Cap { c1 }
    Eq $r.Out.Count 0 'output'; Eq $r.Msg '' 'messages'
    Eq (Last).Cfg $null 'CLAUDE_CONFIG_DIR seen by claude'
    Eq $env:CLAUDE_CONFIG_DIR '/should/vanish' 'env restored'
}
Case 'LaunchersTest.test_c2_and_c3_set_their_config_dir' {
    foreach ($n in 2, 3) {
        $script:Claude.Clear(); $script:BashCalls.Clear()
        & "c$n"
        Eq (Last).Cfg (CfgOf $n) "config dir of c$n"
        Check ($null -eq $env:CLAUDE_CONFIG_DIR) "env not restored after c$n"
        Eq $script:BashCalls.Count 1 'relink calls'
        Eq ($script:BashCalls[0][-1]) (CfgOf $n) 'relink dir argument'
    }
}
Case 'LaunchersTest.test_args_pass_intact' {
    $a = @('--model', 'a b', "it's", '', '-x', '"q"', '$HOME', '*', '--ws', '--resume')
    foreach ($f in 'c1', 'c2', 'c3', 'c') {
        $script:Claude.Clear()
        & $f @a
        Eq ((Last).Args -join '|') ($a -join '|') "args through $f"
        Eq (Last).Args.Count $a.Count "arg count through $f"
    }
}
Case 'ps.args_typed_directly_pass_intact' {
    c1 --model 'a b' --resume
    Eq ((Last).Args -join '|') '--model|a b|--resume' 'args'
}
Case 'LaunchersTest.test_unknown_account_to_run_claude_is_an_error_with_the_text' {
    foreach ($a in '4', '0', 'x') {
        $r = Cap { Invoke-ClaudeAccount $a @() }
        Eq $r.Out.Count 0 'output'
        Eq $r.Msg "unknown account '$a' (use 1, 2 or 3)" "message for $a"
    }
    Eq $script:Claude.Count 0 'claude calls'
}
Case 'LaunchersTest.test_cN_inside_herdr_writes_the_workspace_file_and_reports' {
    InHerdr
    foreach ($n in 1, 2, 3) {
        & "c$n"
        Eq (FileText (Join-Path $script:WsDir 'w26')) "$n`n" "ws file after c$n"
        Eq (@(Reports)[-1].Args[2..6] -join ' ') "w26 --source claude-accounts --token account=c$n" "report after c$n"
    }
    Eq $script:Claude.Count 3 'claude calls'
}
Case 'LaunchersTest.test_cN_outside_herdr_writes_nothing' {
    $env:HERDR_WORKSPACE_ID = 'w26'
    foreach ($n in 1, 2, 3) { & "c$n" }
    NoWsDir
    Eq @(Reports).Count 0 'report calls'
    Eq $script:Claude.Count 3 'claude calls'
}
Case 'LaunchersTest.test_opt_out_skips_the_workspace_write_for_every_launcher' {
    InHerdr; $env:ACCT_NO_WS_DEFAULT = '1'
    foreach ($n in 1, 2, 3) { & "c$n" }
    NoWsDir
    Eq @(Reports).Count 0 'report calls'
    Eq $script:Claude.Count 3 'claude calls'
}
Case 'LaunchersTest.test_cN_starts_claude_even_if_the_workspace_write_fails' {
    InHerdr
    [IO.File]::WriteAllText($script:WsDir, 'blocker')
    foreach ($n in 1, 2, 3) { $r = Cap { & "c$n" }; Eq $r.Out.Count 0 "output of c$n" }
    Eq $script:Claude.Count 3 'claude calls'
}
Case 'LaunchersTest.test_c_runs_the_default_account_and_writes_nothing' {
    c; Eq $script:Claude[-1].Cfg $null 'fallback 1'
    GlobalFile '2'
    c; Eq $script:Claude[-1].Cfg (CfgOf 2) 'global 2'
    WsFile 'w26' "3`n"
    InHerdr
    c; Eq $script:Claude[-1].Cfg (CfgOf 3) 'workspace 3'
    Remove-Item Env:HERDR_ENV; Remove-Item Env:HERDR_WORKSPACE_ID
    c; Eq $script:Claude[-1].Cfg (CfgOf 2) 'outside herdr: global again'
    InHerdr
    foreach ($bad in '9', '', 'x') { WsFile 'w26' $bad; c; Eq $script:Claude[-1].Cfg (CfgOf 2) "garbage <$bad>" }
    Eq (FileText (Join-Path $script:AcctDir 'default')) '2' 'global file untouched'
    Eq @(Reports).Count 0 'report calls'
}
Case 'ps.c1_in_herdr_does_not_change_this_shells_env_or_default' {
    InHerdr; $env:CLAUDE_CONFIG_DIR = '/keep'
    c2; c1
    Eq $env:CLAUDE_CONFIG_DIR '/keep' 'env after c2, c1'
    Eq (FileText (Join-Path $script:WsDir 'w26')) "1`n" 'ws file'
    Check (-not (Test-Path -LiteralPath (Join-Path $script:AcctDir 'default'))) 'global default written by c1'
}

# ---------------------------------------------------------------- startup block
Case 'BashrcLineTest.test_default_picks_config_dir' {
    foreach ($p in @(('2', (CfgOf 2)), ('3', (CfgOf 3)), ('1', $null), ('9', $null))) {
        Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
        GlobalFile $p[0]
        . $Ps1
        Eq $env:CLAUDE_CONFIG_DIR $p[1] "startup with default $($p[0])"
    }
    Remove-Item (Join-Path $script:AcctDir 'default')
    Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
    . $Ps1
    Eq $env:CLAUDE_CONFIG_DIR $null 'startup with no default file'
}
Case 'ps.startup_block_in_a_herdr_pane_uses_the_workspaces_default' {
    GlobalFile '2'; WsFile 'w26' "3`n"
    InHerdr
    . $Ps1
    Eq $env:CLAUDE_CONFIG_DIR (CfgOf 3) 'pane of w26'
    Remove-Item Env:CLAUDE_CONFIG_DIR; $env:HERDR_WORKSPACE_ID = 'w9'
    . $Ps1
    Eq $env:CLAUDE_CONFIG_DIR (CfgOf 2) 'another workspace without a file'
}

# ---------------------------------------------------------------- cdefault
Case 'CdefaultTest.test_print_effective_default' {
    Eq (cdefault) '1' 'no file'
    GlobalFile '2'; Eq (cdefault) '2' 'global'
    WsFile 'w26' "3`n"; InHerdr
    Eq (cdefault) '3' 'workspace'
    Eq (cdefault '') '3' 'empty argument prints too'
    Remove-Item Env:HERDR_ENV; Remove-Item Env:HERDR_WORKSPACE_ID
    Eq (cdefault) '2' 'outside herdr'
}
Case 'CdefaultTest.test_set_global' {
    foreach ($n in '1', '2', '3') {
        $r = Cap { cdefault $n }
        Eq ($r.Out -join '|') "default account: $n" "output for $n"; Eq $r.Msg '' 'messages'
        Eq ((Bytes (Join-Path $script:AcctDir 'default')) -join ',') "$([int][char]$n),10" "bytes for $n (digit LF, no BOM)"
    }
}
Case 'ps.cdefault_with_an_Int32_argument_and_env_of_this_shell' {
    $r = Cap { cdefault 2 }
    Eq ($r.Out -join '|') 'default account: 2' 'cdefault 2 (Int32)'
    Eq (FileText (Join-Path $script:AcctDir 'default')) "2`n" 'file'
    Eq $env:CLAUDE_CONFIG_DIR (CfgOf 2) 'env after 2'
    $null = cdefault 3; Eq $env:CLAUDE_CONFIG_DIR (CfgOf 3) 'env after 3'
    $null = cdefault 1; Eq $env:CLAUDE_CONFIG_DIR $null 'env after 1'
    Eq (cdefault) '1' 'prints what was set'
}
Case 'CdefaultTest.test_set_global_rejects_bad_values' {
    foreach ($bad in '4', 'abc', '0', '12', '--x', 4, 0) {
        $r = Cap { cdefault $bad }
        Eq $r.Out.Count 0 "output for <$bad>"
        Eq $r.Msg 'use 1, 2 or 3' "message for <$bad>"
    }
    Check (-not (Test-Path -LiteralPath (Join-Path $script:AcctDir 'default'))) 'default written'
}
Case 'CdefaultTest.test_ws_current_workspace_in_herdr' {
    InHerdr
    $r = Cap { cdefault --ws 2 }
    Eq ($r.Out -join '|') 'default account of w26: 2' 'output'; Eq $r.Msg '' 'messages'
    Eq (FileText (Join-Path $script:WsDir 'w26')) "2`n" 'ws file'
    Check (-not (Test-Path -LiteralPath (Join-Path $script:AcctDir 'default'))) 'global default written'
    Eq $env:CLAUDE_CONFIG_DIR $null '--ws leaves this shell env alone'
}
Case 'CdefaultTest.test_ws_current_outside_herdr_is_an_error' {
    $env:HERDR_WORKSPACE_ID = 'w26'
    $r = Cap { cdefault --ws 2 }
    Eq $r.Out.Count 0 'output'; Eq $r.Msg 'usage: not inside herdr: give a workspace' 'message'
    NoWsDir
}
Case 'CdefaultTest.test_ws_by_id_number_and_label' {
    SetWs @(@('wA1', 1, 'alpha'), @('wB2', 2, 'beta'))
    foreach ($p in @(@('beta', 'wB2'), @('1', 'wA1'), @('wB2', 'wB2'), @('wZ9', 'wZ9'))) {
        $r = Cap { cdefault --ws $p[0] 3 }
        Eq ($r.Out -join '|') "default account of $($p[1]): 3" "output for $($p[0])"; Eq $r.Msg '' 'messages'
        Eq (FileText (Join-Path $script:WsDir $p[1])) "3`n" "file of $($p[1])"
    }
    $r = Cap { cdefault --ws alpha '2' }
    Eq ($r.Out -join '|') 'default account of wA1: 2' 'string account'
}
Case 'CdefaultTest.test_ws_ambiguous_and_unknown_write_nothing' {
    SetWs @(@('wA1', 1, 'dup'), @('wB2', 2, 'dup'))
    $r = Cap { cdefault --ws dup 2 }
    Eq $r.Out.Count 0 'output'; Check ($r.Msg -like '*ambiguous: dup matches*') "message <$(Show $r.Msg)>"
    $r = Cap { cdefault --ws 'no such' 2 }
    Eq $r.Out.Count 0 'output'; Eq $r.Msg 'no workspace matches no such' 'message'
    NoWsDir
}
Case 'CdefaultTest.test_ws_bad_usage_is_an_error' {
    InHerdr
    foreach ($a in @(@('--ws'), @('--ws', '4'), @('--ws', 'w26', '4'), @('--ws', 'a', 'b', '1'), @('--ws', 'a', '1', 'extra'), @('--ws', 'w26', '1', '2', '3'))) {
        $r = Cap { cdefault @a }
        Eq $r.Out.Count 0 "output for $($a -join ' ')"
        Eq $r.Msg $USAGE "message for $($a -join ' ')"
    }
    NoWsDir
}
Case 'CdefaultTest.test_ws_write_failure_is_an_error' {
    [IO.File]::WriteAllText($script:WsDir, 'blocker')
    $r = Cap { cdefault --ws w26 2 }
    Eq $r.Out.Count 0 'output'; Eq $r.Msg 'could not write the workspace default' 'message'
}

# ---------------------------------------------------------------- Invoke-ClaudeHerdr (real function, cmd.exe as the herdr)
$Cmd = $env:ComSpec
Case 'ps.Invoke-ClaudeHerdr_ok_returns_stdout' -RealHerdr {
    $script:HerdrExe = $Cmd
    $r = Cap { Invoke-ClaudeHerdr @('/c', 'echo', 'hello') 5 }
    Eq $r.Out.Count 1 'outputs'; Check ($r.Out[0] -is [string] -and $r.Out[0].Trim() -ceq 'hello') "stdout <$(Show $r.Out)>"
    Eq $r.Msg '' 'messages'
}
Case 'ps.Invoke-ClaudeHerdr_nonzero_exit_is_null' -RealHerdr {
    $script:HerdrExe = $Cmd
    $r = Cap { Invoke-ClaudeHerdr @('/c', 'echo out& exit 3') 5 }
    Eq $r.Out.Count 0 'no output (null)'; Eq $r.Msg '' 'messages'
}
Case 'ps.Invoke-ClaudeHerdr_timeout_kills_the_process_and_is_null' -RealHerdr {
    $script:HerdrExe = $Cmd
    $t = Get-Date
    $r = Cap { Invoke-ClaudeHerdr @('/c', 'ping -n 30 127.0.0.1 >nul') 1 }
    $sec = ((Get-Date) - $t).TotalSeconds
    Check ($sec -lt 8) "returned after $sec s (timeout was 1)"
    Eq $r.Out.Count 0 'output'; Eq $r.Msg '' 'messages'
    Start-Sleep -Milliseconds 500
    $left = @(Get-CimInstance Win32_Process -Filter "Name='PING.EXE'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*-n 30 127.0.0.1*' })
    Eq $left.Count 0 'ping children left running (Kill($true) must take the tree)'
}
Case 'ps.Invoke-ClaudeHerdr_missing_exe_never_throws_or_prints' -RealHerdr {
    $script:HerdrExe = 'C:\no-such-dir-ca\herdr.exe'
    $r = Cap { Invoke-ClaudeHerdr @('workspace', 'list') 5 }
    Eq $r.Out.Count 0 'output'; Eq $r.Msg '' 'messages'
    $script:HerdrExe = $null
    $savedPath = $env:PATH
    try { $env:PATH = 'C:\no-such-dir-ca'; $r = Cap { Invoke-ClaudeHerdr @('workspace', 'list') 5 } } finally { $env:PATH = $savedPath }
    Eq $r.Out.Count 0 'output with no herdr on PATH'; Eq $r.Msg '' 'messages with no herdr on PATH'
}
