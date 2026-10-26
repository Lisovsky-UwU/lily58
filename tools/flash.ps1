param(
    [Parameter(Mandatory)] [string]$Uf2,
    [int]$TimeoutSec = 120
)

# Waits for the RP2040 boot ROM drive (label RPI-RP2) and copies the firmware onto it.
$deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt $deadline) {
    $vol = Get-Volume | Where-Object { $_.FileSystemLabel -eq 'RPI-RP2' -and $_.DriveLetter }
    if ($vol) {
        $dst = "$($vol.DriveLetter):\"
        Write-Output "RPI-RP2 found at $dst, info: $((Get-Content "$dst\INFO_UF2.TXT" -ErrorAction SilentlyContinue) -join ' | ')"
        Copy-Item -LiteralPath $Uf2 -Destination $dst
        Write-Output "copied $(Split-Path $Uf2 -Leaf) at $(Get-Date -Format HH:mm:ss)"
        exit 0
    }
    Start-Sleep -Milliseconds 300
}
Write-Output "timeout: RPI-RP2 drive did not appear in $TimeoutSec s"
exit 1
