# Job Hunter Daily Automation Script
# 每日自动运行脚本

param(
    [switch]$AutoApply = $false,
    [switch]$DryRun = $true
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "C:\Users\huang\AppData\Local\Programs\Python\Python312\python.exe"
$LogDir = "$ProjectDir\logs"

# 创建日志目录
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$LogFile = "$LogDir\daily_$Timestamp.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Job Hunter Daily Automation" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "Auto Apply: $($AutoApply)" -ForegroundColor Cyan
Write-Host "Log: $LogFile" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 构建命令
if ($AutoApply) {
    $Cmd = "$Python job_hunter_cli.py daily --auto-apply"
} else {
    $Cmd = "$Python job_hunter_cli.py daily"
}

Write-Host "Executing: $Cmd" -ForegroundColor Yellow
Write-Host ""

# 执行并记录日志
& $Python "$ProjectDir\job_hunter_cli.py" daily @($AutoApply ? "--auto-apply" : $null) 2>&1 | Tee-Object -FilePath $LogFile

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Daily run completed!" -ForegroundColor Green
Write-Host "Log saved to: $LogFile" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 发送通知（如果有新的高优先级职位）
$DataDir = "$ProjectDir\data"
$LatestAnalysis = Get-ChildItem -Path $DataDir -Filter "analysis_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($LatestAnalysis) {
    try {
        $Jobs = Get-Content $LatestAnalysis.FullName | ConvertFrom-Json
        $HighPriority = $Jobs | Where-Object { $_.score -ge 7.5 }
        
        if ($HighPriority.Count -gt 0) {
            Write-Host ""
            Write-Host "Found $($HighPriority.Count) high-priority jobs!" -ForegroundColor Magenta
        }
    } catch {
        # 忽略解析错误
    }
}
