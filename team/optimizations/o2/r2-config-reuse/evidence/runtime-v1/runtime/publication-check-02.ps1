param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [Parameter(Mandatory=$true)][string]$Report
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
if (-not [System.IO.Path]::IsPathFullyQualified($Repository) -or -not [System.IO.Path]::IsPathFullyQualified($Report)) {
    throw 'Use absolute publication paths'
}
Set-Location -LiteralPath $Repository
if (Test-Path -LiteralPath $Report) { throw 'Use a new publication report' }
$git = (Get-Command git.exe -ErrorAction Stop).Source
$longPaths = (& $git config --get core.longpaths).Trim()
if ($LASTEXITCODE -ne 0 -or $longPaths -ne 'true') { throw 'Native Git long paths must already be enabled' }
$head = (& $git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne '43e562d5e174763d9469b6c1c2124df0d60dc576') { throw 'Publication base changed' }
$branch = (& $git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne 'work/r2s3-runtime-20261024-1818') { throw 'Unexpected work branch' }
$module = 'team/optimizations/o2/r2-config-reuse'
$fixed = @(
    '.gitattributes','runtime_candidate.py','runtime_gate.py','runtime_experiment.py','runtime_evidence.py',
    'test_runtime.py','test_runtime_evidence.py','RUNTIME_CONTRACT.md','c_api.py','c_evidence.py','library.py',
    'test_c_api.py','C_CONTRACT.md','RUNTIME_README.md','usage_check.py','RUNTIME_RESULT.md',
    'public/gemv.S','public/gemv.h','public/manifest.json','README.md'
) | ForEach-Object { "$module/$_" }
$fixed += @('team/docs/development-route-current.md','开发计分板.md')
$prefix = $module + '/evidence/runtime-v1/'
$expected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($name in $fixed) {
    if (-not (Test-Path -LiteralPath (Join-Path $Repository $name) -PathType Leaf)) { throw "Missing publication file: $name" }
    [void]$expected.Add($name)
}
$root = (Resolve-Path -LiteralPath $Repository).Path.TrimEnd('\')
if (-not [System.IO.Path]::GetFullPath($Report).Equals(
        [System.IO.Path]::GetFullPath((Join-Path $root ($prefix + 'reports/publication-check-01.json'))),
        [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Report must be the new publication reports/publication-check-01.json, outside sealed archives'
}
$evidence = Join-Path $Repository $prefix
foreach ($file in Get-ChildItem -LiteralPath $evidence -Recurse -Force) {
    if (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked publication entry' }
    if (-not $file.PSIsContainer) {
        $relative = $file.FullName.Substring($root.Length + 1).Replace('\','/')
        if ($relative -match '(^|/)__pycache__/|\.pyc$') { throw 'Incidental Python cache in publication' }
        [void]$expected.Add($relative)
    }
}
$staged = @(& $git -c core.quotepath=false diff --cached --name-only)
if ($LASTEXITCODE -ne 0 -or $staged.Count -ne $expected.Count) {
    throw "Staged inventory differs: $($staged.Count) vs $($expected.Count)"
}
foreach ($name in $staged) {
    if (-not $expected.Contains($name) -or $name -match '["\r\n\t]') { throw "Unexpected staged path: $name" }
}
$entries = @(& $git -c core.quotepath=false ls-files --stage -- $module 'team/docs/development-route-current.md' '开发计分板.md')
if ($LASTEXITCODE -ne 0) { throw 'Cannot read native Git index' }
$index = @{}
foreach ($entry in $entries) {
    if ($entry -notmatch '^([0-7]{6}) ([0-9a-f]{40}) ([0-3])\t(.+)$') { throw 'Unexpected Git index row' }
    $name = $Matches[4]
    if ($expected.Contains($name)) {
        if ($Matches[1] -ne '100644' -or $Matches[3] -ne '0' -or $index.ContainsKey($name)) {
            throw "Publication entry must be one regular stage-0 blob: $name"
        }
        $index[$name] = $Matches[2]
    }
}
if ($index.Count -ne $expected.Count) { throw 'Index inventory is incomplete' }
# This hashes raw working-file bytes. No text/EOL exception is silently accepted.
$objects = @($staged | & $git hash-object --no-filters --stdin-paths)
if ($LASTEXITCODE -ne 0 -or $objects.Count -ne $staged.Count) { throw 'Raw Git hash inventory differs' }
$rows = [System.Collections.Generic.List[object]]::new()
$byPath = @{}
$total = [long]0
for ($i=0; $i -lt $staged.Count; $i++) {
    $name = $staged[$i]
    if ($objects[$i] -ne $index[$name]) { throw "Staged raw bytes differ: $name" }
    $file = Join-Path $Repository $name
    $bytes = [System.IO.File]::ReadAllBytes('\\?\' + $file)
    $engine = [System.Security.Cryptography.SHA256]::Create()
    try { $sha = [System.BitConverter]::ToString($engine.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() }
    finally { $engine.Dispose() }
    $row = [ordered]@{ path=$name; bytes=$bytes.Length; sha256=$sha; staged_blob=$index[$name]; mode='100644'; stage=0 }
    $rows.Add($row)
    $byPath[$name] = $row
    $total += $bytes.Length
}
$archives = [System.Collections.Generic.List[object]]::new()
foreach ($name in @('probe-archive','matrix-archive','c-archive')) {
    $archivePrefix = $prefix + $name + '/'
    $manifestPath = $archivePrefix + 'archive-manifest.json'
    $manifest = Get-Content -LiteralPath (Join-Path $Repository $manifestPath) -Raw -Encoding UTF8 | ConvertFrom-Json
    $payloads = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($item in $manifest.files) {
        $stored = [string]$item.stored
        if ([System.IO.Path]::IsPathRooted($stored) -or $stored -match '(^|/)\.\.(/|$)|\\|[\r\n\t]') {
            throw 'Unsafe archive payload path'
        }
        $path = $archivePrefix + $stored
        if (-not $payloads.Add($path) -or -not $byPath.ContainsKey($path)) { throw "Missing/duplicate staged archive payload: $path" }
        if ($byPath[$path].sha256 -ne $item.stored_sha256 -or $byPath[$path].bytes -ne $item.stored_bytes) {
            throw "Staged archive bytes differ from manifest: $path"
        }
    }
    $actual = @($staged | Where-Object { $_.StartsWith($archivePrefix, [System.StringComparison]::Ordinal) })
    if ($actual.Count -ne ($payloads.Count + 3)) { throw "Archive inventory is not closed: $name" }
    foreach ($suffix in @('archive-manifest.json','archive-manifest.sha256','archive-check.json')) {
        if (-not $byPath.ContainsKey($archivePrefix + $suffix)) { throw 'Archive metadata missing from index' }
    }
    $recorded = (Get-Content -LiteralPath (Join-Path $Repository ($archivePrefix + 'archive-manifest.sha256')) -Raw -Encoding UTF8).Trim()
    if ($recorded -ne ($byPath[$manifestPath].sha256 + '  archive-manifest.json')) { throw 'Manifest SHA file differs' }
    $archives.Add([ordered]@{name=$name;manifest_sha256=$byPath[$manifestPath].sha256;staged_payloads=$payloads.Count;closed_inventory=$true})
}
$null = & $git diff --quiet
if ($LASTEXITCODE -ne 0) { throw 'Unstaged tracked edits remain' }
$check = @(& $git diff --cached --check 2>&1 | ForEach-Object { "$_" })
$checkCode = $LASTEXITCODE
if ($checkCode -ne 0) { throw ('Staged whitespace check failed: ' + ($check -join "`n")) }
$reportData = [ordered]@{
    status='S3_NATIVE_WINDOWS_STAGED_IDENTITIES_PASS'
    created_utc=[DateTimeOffset]::UtcNow.ToString('o')
    repository=$root
    branch=$branch
    source_base=$head
    git_executable=$git
    core_longpaths=$longPaths
    files=$rows.Count
    bytes=$total
    inventory_exact=$true
    index_matches_raw_file_bytes=$true
    text_normalization_exceptions=0
    method='Native Windows Git: exact changed-file inventory, regular stage-0 blobs, raw hash-object and SHA256, complete archive payload closure'
    archives=$archives
    diff_check_exit_code=$checkCode
    report_not_in_checked_inventory=$true
    rows=$rows
}
[System.IO.File]::WriteAllText($Report, ($reportData | ConvertTo-Json -Depth 8) + "`n", [System.Text.UTF8Encoding]::new($false))
[ordered]@{status=$reportData.status;files=$rows.Count;bytes=$total;archives=$archives;report=$Report} | ConvertTo-Json -Depth 5
