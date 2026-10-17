# PowerShell side of the three-account launchers (bash side: ~/.claude-accounts/bin).
# Account 1 = ~/.claude (CLAUDE_CONFIG_DIR unset), account 2 = ~/.claude-b, account 3 = ~/.claude-3.
$script:AcctHome = Join-Path $HOME '.claude-accounts'
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

function Get-ClaudeDefaultAccount {
    $f = Join-Path $script:AcctHome 'default'
    if (Test-Path $f) { (Get-Content $f -Raw).Trim() } else { '1' }
}

function c1 { Invoke-ClaudeAccount '1' $args }
function c2 { Invoke-ClaudeAccount '2' $args }
function c3 { Invoke-ClaudeAccount '3' $args }
function c  { Invoke-ClaudeAccount (Get-ClaudeDefaultAccount) $args }

function cdefault {
    if (-not $args) { return Get-ClaudeDefaultAccount }
    if ($args[0] -notin '1', '2', '3') { Write-Error 'use 1, 2 or 3'; return }
    # No BOM/CRLF: the bash launchers read this same file.
    [IO.File]::WriteAllText((Join-Path $script:AcctHome 'default'), "$($args[0])`n")
    $dir = @{ '2' = '.claude-b'; '3' = '.claude-3' }["$($args[0])"]
    if ($dir) { $env:CLAUDE_CONFIG_DIR = Join-Path $HOME $dir }
    else { Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue }
    "default account: $($args[0])"
}

# Plain `claude` follows the default account in shells opened after cdefault.
switch (Get-ClaudeDefaultAccount) {
    '2' { $env:CLAUDE_CONFIG_DIR = Join-Path $HOME '.claude-b' }
    '3' { $env:CLAUDE_CONFIG_DIR = Join-Path $HOME '.claude-3' }
}
