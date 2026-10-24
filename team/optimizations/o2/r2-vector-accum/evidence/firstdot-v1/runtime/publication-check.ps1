param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [Parameter(Mandatory=$true)][string]$Report
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
if (-not [System.IO.Path]::IsPathFullyQualified($Repository) -or -not [System.IO.Path]::IsPathFullyQualified($Report)) { throw 'Use absolute publication paths' }
Set-Location -LiteralPath $Repository
if (Test-Path -LiteralPath $Report) { throw 'Use a new publication report' }
$git = (Get-Command git.exe -ErrorAction Stop).Source
$longPaths = (& $git config --get core.longpaths).Trim()
if ($LASTEXITCODE -ne 0 -or $longPaths -ne 'true') { throw 'Native Git long paths must already be enabled' }
$head = (& $git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne '137b44befb041439a018a1079577cc000df1ee03') { throw 'Publication base changed' }
$branch = (& $git branch --show-current).Trim()
if ($branch -ne 'work/r2s1-firstdot-20261024-1458') { throw 'Unexpected work branch' }
$module = 'team/optimizations/o2/r2-vector-accum'
$fixed = @(
    'firstdot_candidate.py','firstdot_gate.py','firstdot_experiment.py',
    'firstdot_evidence.py','firstdot_c_api.py','firstdot_c_evidence.py','firstdot_library.py',
    'test_firstdot.py','test_firstdot_evidence.py','test_firstdot_c_api.py',
    'FIRSTDOT_CONTRACT.md','FIRSTDOT_C_CONTRACT.md','FIRSTDOT_README.md','FIRSTDOT_RESULT.md',
    'firstdot/public/gemv.S','firstdot/public/gemv.h','firstdot/public/manifest.json','README.md'
) | ForEach-Object { "$module/$_" }
$fixed += @('team/docs/development-route-current.md','开发计分板.md')
$prefix = $module + '/evidence/firstdot-v1/'
$expected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($name in $fixed) {
    if (-not (Test-Path -LiteralPath (Join-Path $Repository $name) -PathType Leaf)) { throw "Missing publication file: $name" }
    [void]$expected.Add($name)
}
$root = (Resolve-Path -LiteralPath $Repository).Path.TrimEnd('\')
$evidence = Join-Path $Repository $prefix
foreach ($file in Get-ChildItem -LiteralPath $evidence -File -Recurse) {
    if (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked publication file' }
    $relative = $file.FullName.Substring($root.Length + 1).Replace('\','/')
    [void]$expected.Add($relative)
}
$staged = @(& $git -c core.quotepath=false diff --cached --name-only)
if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate staged changes' }
if ($staged.Count -ne $expected.Count) { throw "Staged inventory differs: $($staged.Count) vs $($expected.Count)" }
foreach ($name in $staged) {
    if (-not $expected.Contains($name) -or $name -match '["\r\n\t]') { throw "Unexpected staged path: $name" }
}
$entries = @(& $git -c core.quotepath=false ls-files --stage)
if ($LASTEXITCODE -ne 0) { throw 'Cannot read native Git index' }
$index = @{}
foreach ($entry in $entries) {
    if ($entry -notmatch '^([0-7]{6}) ([0-9a-f]{40}) ([0-3])\t(.+)$') { throw "Unexpected Git index row" }
    $name = $Matches[4]
    if ($expected.Contains($name)) {
        if ($Matches[3] -ne '0' -or $index.ContainsKey($name)) { throw 'Unmerged index' }
        $index[$name] = $Matches[2]
    }
}
# --no-filters makes the hash represent raw working-file bytes, without EOL conversion.
$objects = @($staged | & $git hash-object --no-filters --stdin-paths)
if ($LASTEXITCODE -ne 0 -or $objects.Count -ne $staged.Count) { throw 'Raw Git hash inventory differs' }
$rows = [System.Collections.Generic.List[object]]::new()
$total = [long]0
$normalized = [System.Collections.Generic.List[string]]::new()
for ($i=0; $i -lt $staged.Count; $i++) {
    $name = $staged[$i]
    if (-not $index.ContainsKey($name)) { throw "Staged path missing: $name" }
    $file = Join-Path $Repository $name
    $bytes = [System.IO.File]::ReadAllBytes('\\?\' + $file)
    $engine = [System.Security.Cryptography.SHA256]::Create()
    try { $sha = [System.BitConverter]::ToString($engine.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() }
    finally { $engine.Dispose() }
    $stagedSha = $sha
    $normalization = 'none'
    if ($objects[$i] -ne $index[$name]) {
        if ($name -ne '开发计分板.md') { throw "Staged raw bytes differ: $name" }
        # Preserve the existing Windows CRLF document; verify its known Git LF form exactly.
        $utf8 = [System.Text.UTF8Encoding]::new($false,$true)
        $rawText = $utf8.GetString($bytes)
        if ($rawText -notmatch "`r`n" -or $rawText -match "(?<!`r)`n|`r(?!`n)") { throw 'Unexpected scoreboard line endings' }
        $canonical = $utf8.GetBytes($rawText.Replace("`r`n","`n"))
        $header = [System.Text.Encoding]::ASCII.GetBytes("blob $($canonical.Length)" + [char]0)
        $payload = [byte[]]::new($header.Length + $canonical.Length)
        [System.Array]::Copy($header,0,$payload,0,$header.Length)
        [System.Array]::Copy($canonical,0,$payload,$header.Length,$canonical.Length)
        $gitHash = [System.Security.Cryptography.SHA1]::Create()
        $contentHash = [System.Security.Cryptography.SHA256]::Create()
        try {
            $canonicalBlob = [System.BitConverter]::ToString($gitHash.ComputeHash($payload)).Replace('-','').ToLowerInvariant()
            $stagedSha = [System.BitConverter]::ToString($contentHash.ComputeHash($canonical)).Replace('-','').ToLowerInvariant()
        } finally { $gitHash.Dispose(); $contentHash.Dispose() }
        if ($canonicalBlob -ne $index[$name]) { throw 'Scoreboard staged bytes differ beyond CRLF normalization' }
        $normalization = 'existing Windows CRLF to Git LF; scoreboard only'
        $normalized.Add($name)
    }
    $total += $bytes.Length
    $rows.Add([ordered]@{ path=$name; bytes=$bytes.Length; sha256=$sha; staged_sha256=$stagedSha; normalization=$normalization; staged_blob=$index[$name] })
}
$null = & $git diff --quiet
if ($LASTEXITCODE -ne 0) { throw 'Unstaged tracked edits remain' }
$check = @(& $git diff --cached --check 2>&1 | ForEach-Object { "$_" })
$checkCode = $LASTEXITCODE
$reportData = [ordered]@{
    status='FIRSTDOT_NATIVE_WINDOWS_STAGED_IDENTITIES_PASS'
    created_utc=[DateTimeOffset]::UtcNow.ToString('o')
    repository=$root
    branch=$branch
    source_base=$head
    git_executable=$git
    core_longpaths=$longPaths
    files=$rows.Count
    bytes=$total
    inventory_exact=$true
    index_matches_expected_file_bytes=$true
    raw_byte_matches=($rows.Count - $normalized.Count)
    normalized_text_paths=$normalized
    method='Native Windows Git index vs raw hash-object and SHA256 for every source/evidence file; only existing root scoreboard CRLF is canonically verified as Git LF'
    diff_check_exit_code=$checkCode
    diff_check_output=$check
    report_not_in_checked_inventory=$true
    rows=$rows
}
[System.IO.File]::WriteAllText($Report, ($reportData | ConvertTo-Json -Depth 8) + "`n", [System.Text.UTF8Encoding]::new($false))
[ordered]@{status=$reportData.status;files=$rows.Count;bytes=$total;diff_check_exit_code=$checkCode;diff_check_output=$check;report=$Report} | ConvertTo-Json -Depth 4
