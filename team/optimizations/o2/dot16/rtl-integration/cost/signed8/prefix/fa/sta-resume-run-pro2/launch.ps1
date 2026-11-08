$ErrorActionPreference = 'Stop'
$faLaunchPath = 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runs\dot16-prefix-fa-20261108-main\sta-resume-run-pro2\launch.py'
if ((Get-Item -LiteralPath $faLaunchPath).Length -ne 4471 -or (Get-FileHash -LiteralPath $faLaunchPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '7ef4e53e3c492adfd2daeeb43b0d6aa004c62aae51e54379cbd688240873581d') { throw 'fixed STA launch wrapper changed' }
$faLaunchText = [System.IO.File]::ReadAllText($faLaunchPath, [System.Text.Encoding]::UTF8)
& wsl.exe -d Ubuntu-22.04 --exec /usr/bin/taskset -c 3 /usr/bin/nice -n 5 /usr/bin/setsid --wait /usr/bin/python3 -B -c $faLaunchText
exit $LASTEXITCODE
