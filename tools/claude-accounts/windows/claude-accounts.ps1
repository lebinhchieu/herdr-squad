# PowerShell side of the three-account launchers (bash side: ~/.claude-accounts/bin).
# Account 1 = ~/.claude (CLAUDE_CONFIG_DIR unset), account 2 = ~/.claude-b, account 3 = ~/.claude-3.
# CLAUDE_ACCOUNTS_HOME lets tests and scratch runs use a folder other than the real one; read once, at dot-source.
$script:AcctHome = $env:CLAUDE_ACCOUNTS_HOME ? $env:CLAUDE_ACCOUNTS_HOME : (Join-Path $HOME '.claude-accounts')
$script:WsDir    = Join-Path $script:AcctHome 'workspace-default'
$script:GitBash  = 'C:\Program Files\Git\bin\bash.exe'

function Invoke-ClaudeAccount([string]$Account, [object[]]$ClaudeArgs) {
    $saved = $env:CLAUDE_CONFIG_DIR
    try {
        switch ($Account) {
            '1' { Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue }
            { $_ -in '2', '3' } {
                $dir = Join-Path $HOME ($Account -eq '2' ? '.claude-b' : '.claude-3')
                # Re-join hardlinks Claude may have split by rewriting a shared file.
                & $script:GitBash -lc '. ~/.claude-accounts/lib.sh && d=$(cygpath -u "$1") && mkdir -p "$d" && relink "$d"' _ $dir
                $env:CLAUDE_CONFIG_DIR = $dir
            }
            default { Write-Error "unknown account '$Account' (use 1, 2 or 3)"; return }
        }
        & claude @ClaudeArgs
    } finally {
        if ($null -eq $saved) { Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue }
        else { $env:CLAUDE_CONFIG_DIR = $saved }
    }
}

# The id becomes a file name: \z not $ (a trailing newline passes $), -cmatch because bash is case-sensitive.
function Test-WsId([string]$Id) { $Id -cmatch '^w[0-9A-Za-z]+\z' }

# Delete and ReadWrite sharing: a reader must not make a writer's rename fail on NTFS.
function Read-ClaudeSmallFile([string]$Path) {
    try {
        $fs = [IO.FileStream]::new($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]'ReadWrite,Delete')
        $sr = [IO.StreamReader]::new($fs)
        try { $sr.ReadToEnd() } finally { $sr.Dispose() }
    } catch { $null }
}

# Stdout on exit 0, else $null; never throws or prints. The timeout keeps a stuck herdr from holding up c1.
function Invoke-ClaudeHerdr([string[]]$HerdrArgs, [int]$TimeoutSec) {
    if (-not $script:HerdrExe) {
        $script:HerdrExe = (Get-Command herdr -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    }
    if (-not $script:HerdrExe) { return $null }
    $p = $null
    try {
        $psi = [Diagnostics.ProcessStartInfo]::new($script:HerdrExe)
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        foreach ($a in $HerdrArgs) { $psi.ArgumentList.Add($a) }
        $p = [Diagnostics.Process]::Start($psi)
        # Read both pipes before waiting: a full pipe would block herdr while we wait for it.
        $out = $p.StandardOutput.ReadToEndAsync()
        $null = $p.StandardError.ReadToEndAsync()
        if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill($true); return $null }
        if ($p.ExitCode -ne 0) { return $null }
        $out.Result
    } catch { $null } finally { if ($p) { $p.Dispose() } }
}

# The workspace objects of `herdr workspace list`, or $null when herdr is missing, slow or answers nonsense.
function Get-ClaudeWorkspaceList {
    $json = Invoke-ClaudeHerdr @('workspace', 'list') 5
    if (-not $json) { return $null }
    try {
        $list = ($json | ConvertFrom-Json -ErrorAction Stop).result.workspaces
        if ($null -eq $list) { $null } else { , @($list) }
    } catch { $null }
}

function Get-ClaudeGlobalDefault {
    $v = "$(Read-ClaudeSmallFile (Join-Path $script:AcctHome 'default'))".Trim()
    if ($v -in '1', '2', '3') { $v } else { '1' }
}

# Inside herdr the workspace's own default wins, else the global one.
function Get-ClaudeDefaultAccount {
    if ($env:HERDR_ENV -eq '1' -and (Test-WsId $env:HERDR_WORKSPACE_ID)) {
        $v = "$(Read-ClaudeSmallFile (Join-Path $script:WsDir $env:HERDR_WORKSPACE_ID))".Trim()
        if ($v -in '1', '2', '3') { return $v }
    }
    Get-ClaudeGlobalDefault
}

# Workspace id, panel number or label -> id. Tiers, first with a hit wins: id, panel number, label.
# Several hits in the winning tier: candidates on stderr, $null. No hit: an id-shaped ref is taken as a raw id.
function Resolve-ClaudeWorkspace([string]$Ref) {
    if ([string]::IsNullOrWhiteSpace($Ref)) { Write-Error "no workspace matches $Ref"; return $null }
    $list = Get-ClaudeWorkspaceList
    if ($list) {
        $hits = @($list | Where-Object { $_.workspace_id -ceq $Ref })
        if (-not $hits -and $Ref -cmatch '^[0-9]+\z') { $hits = @($list | Where-Object { "$($_.number)" -ceq $Ref }) }
        if (-not $hits) { $hits = @($list | Where-Object { $_.label -ceq $Ref }) }
        if ($hits.Count -eq 1 -and (Test-WsId $hits[0].workspace_id)) { return [string]$hits[0].workspace_id }
        if ($hits.Count -gt 1) {
            $lines = $hits | ForEach-Object { "$($_.workspace_id) (panel $($_.number)) $($_.label)" }
            Write-Error ("ambiguous: $Ref matches`n" + ($lines -join "`n"))
            return $null
        }
    }
    if (Test-WsId $Ref) { return $Ref }
    Write-Error "no workspace matches $Ref"
    $null
}

# Display-only token for the herdr spaces panel; result ignored. The epoch-ms seq makes herdr drop a late older report.
function Send-ClaudeWorkspaceAccount([string]$Id, [string]$Acct) {
    $seq = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $null = Invoke-ClaudeHerdr @('workspace', 'report-metadata', $Id, '--source', 'claude-accounts', '--token', "account=c$Acct", '--seq', "$seq") 3
}

# One file per workspace + tmp and move = parallel runs cannot lose each other's update.
# No $Id: the current workspace, and only inside herdr. $true means nothing went wrong (nothing to write counts).
function Set-ClaudeWorkspaceDefault([string]$Acct, [string]$Id) {
    if ($Acct -notin '1', '2', '3') { return $false }
    if (-not $Id) {
        if ($env:HERDR_ENV -ne '1') { return $true }
        $Id = $env:HERDR_WORKSPACE_ID
    }
    if (-not (Test-WsId $Id)) { return $true }
    $tmp = Join-Path $script:WsDir ".tmp.$([IO.Path]::GetRandomFileName())"
    try {
        $null = New-Item -ItemType Directory -Force -Path $script:WsDir
        # No BOM/CRLF: the bash launchers read this same file.
        [IO.File]::WriteAllText($tmp, "$Acct`n", [Text.UTF8Encoding]::new($false))
        $dest = Join-Path $script:WsDir $Id
        # NTFS refuses a rename over a file another process has open at that instant.
        for ($i = 1; ; $i++) {
            try { [IO.File]::Move($tmp, $dest, $true); break }
            catch [IO.IOException], [UnauthorizedAccessException] { if ($i -ge 5) { throw }; Start-Sleep -Milliseconds 40 }
        }
    } catch {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        return $false
    }
    Send-ClaudeWorkspaceAccount $Id $Acct
    # Drop files of workspaces herdr no longer lists; do nothing if the list failed or is empty.
    $list = Get-ClaudeWorkspaceList
    if ($list) {
        $ids = @($list | ForEach-Object { $_.workspace_id })
        Get-ChildItem -LiteralPath $script:WsDir -Filter 'w*' -File -ErrorAction SilentlyContinue |
            Where-Object { (Test-WsId $_.Name) -and $_.Name -cne $Id -and $ids -cnotcontains $_.Name } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
    $true
}

function c1 { if ($env:ACCT_NO_WS_DEFAULT -ne '1') { $null = Set-ClaudeWorkspaceDefault '1' }; Invoke-ClaudeAccount '1' $args }
function c2 { if ($env:ACCT_NO_WS_DEFAULT -ne '1') { $null = Set-ClaudeWorkspaceDefault '2' }; Invoke-ClaudeAccount '2' $args }
function c3 { if ($env:ACCT_NO_WS_DEFAULT -ne '1') { $null = Set-ClaudeWorkspaceDefault '3' }; Invoke-ClaudeAccount '3' $args }
function c  { Invoke-ClaudeAccount (Get-ClaudeDefaultAccount) $args }

function cdefault {
    # PowerShell passes 2 as an Int32; compare everything as strings.
    $a = @($args | ForEach-Object { "$_" })
    if (-not $a -or $a[0] -eq '') { return Get-ClaudeDefaultAccount }
    if ($a[0] -ceq '--ws') {
        $usage = 'usage: cdefault --ws [<workspace id|panel number|label>] <1|2|3>'
        if ($a.Count -eq 2 -and $a[1] -cmatch '^[123]\z') {
            if (-not ($env:HERDR_ENV -eq '1' -and (Test-WsId $env:HERDR_WORKSPACE_ID))) { Write-Error 'usage: not inside herdr: give a workspace'; return }
            $id = $env:HERDR_WORKSPACE_ID
        } elseif ($a.Count -eq 3 -and $a[2] -cmatch '^[123]\z') {
            $id = Resolve-ClaudeWorkspace $a[1]
            if (-not $id) { return }
        } else { Write-Error $usage; return }
        if (-not (Set-ClaudeWorkspaceDefault $a[-1] $id)) { Write-Error 'could not write the workspace default'; return }
        return "default account of ${id}: $($a[-1])"
    }
    if ($a[0] -notin '1', '2', '3') { Write-Error 'use 1, 2 or 3'; return }
    # No BOM/CRLF: the bash launchers read this same file.
    [IO.File]::WriteAllText((Join-Path $script:AcctHome 'default'), "$($a[0])`n")
    $dir = @{ '2' = '.claude-b'; '3' = '.claude-3' }[$a[0]]
    if ($dir) { $env:CLAUDE_CONFIG_DIR = Join-Path $HOME $dir }
    else { Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue }
    "default account: $($a[0])"
}

# Plain `claude` follows the default account in shells opened after cdefault.
switch (Get-ClaudeDefaultAccount) {
    '2' { $env:CLAUDE_CONFIG_DIR = Join-Path $HOME '.claude-b' }
    '3' { $env:CLAUDE_CONFIG_DIR = Join-Path $HOME '.claude-3' }
}
