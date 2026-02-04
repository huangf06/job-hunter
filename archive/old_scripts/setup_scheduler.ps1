# Setup Windows Task Scheduler for Job Hunter
# 设置 Windows 定时任务

param(
    [int]$Hour = 10,
    [int]$Minute = 0,
    [switch]$AutoApply = $false,
    [switch]$Remove = $false
)

$TaskName = "JobHunter-Daily"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PowerShell = "powershell.exe"
$ScriptPath = "$ProjectDir\run_daily.ps1"

# 参数
$Arguments = if ($AutoApply) {
    "-ExecutionPolicy Bypass -File `"$ScriptPath`" -AutoApply"
} else {
    "-ExecutionPolicy Bypass -File `"$ScriptPath`""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Job Hunter Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($Remove) {
    # 删除现有任务
    Write-Host "Removing existing task '$TaskName'..." -ForegroundColor Yellow
    try {
        schtasks /delete /tn $TaskName /f 2>$null
        Write-Host "Task removed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "No existing task found or removal failed." -ForegroundColor Yellow
    }
    return
}

# 检查现有任务
$ExistingTask = schtasks /query /tn $TaskName 2>$null
if ($ExistingTask) {
    Write-Host "Task '$TaskName' already exists." -ForegroundColor Yellow
    Write-Host "Use -Remove switch to remove it first, or update the existing task." -ForegroundColor Yellow
    Write-Host ""
    $Overwrite = Read-Host "Do you want to overwrite? (y/n)"
    if ($Overwrite -ne "y") {
        Write-Host "Setup cancelled." -ForegroundColor Red
        return
    }
    schtasks /delete /tn $TaskName /f 2>$null
}

# 创建任务
Write-Host "Creating scheduled task..." -ForegroundColor Yellow
Write-Host "  Task Name: $TaskName" -ForegroundColor Gray
Write-Host "  Schedule: Daily at $Hour`:$($Minute.ToString().PadLeft(2,'0'))" -ForegroundColor Gray
Write-Host "  Auto Apply: $($AutoApply)" -ForegroundColor Gray
Write-Host "  Script: $ScriptPath" -ForegroundColor Gray
Write-Host ""

# 创建 XML 配置文件
$XmlContent = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Job Hunter Daily Automation - Automated job search and application</Description>
    <Author>JobHunter</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$(Get-Date -Format "yyyy-MM-dd")T$($Hour.ToString().PadLeft(2,'0')):$($Minute.ToString().PadLeft(2,'0')):00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$PowerShell</Command>
      <Arguments>$Arguments</Arguments>
      <WorkingDirectory>$ProjectDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$XmlPath = "$env:TEMP\JobHunter_Task.xml"
$XmlContent | Out-File -FilePath $XmlPath -Encoding Unicode

# 导入任务
try {
    schtasks /create /tn $TaskName /xml $XmlPath /f | Out-Null
    Remove-Item $XmlPath -ErrorAction SilentlyContinue
    
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName" -ForegroundColor Gray
    Write-Host "  Schedule: Daily at $Hour`:$($Minute.ToString().PadLeft(2,'0'))" -ForegroundColor Gray
    Write-Host "  Working Directory: $ProjectDir" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  Run now:     schtasks /run /tn $TaskName" -ForegroundColor Gray
    Write-Host "  View status: schtasks /query /tn $TaskName /v" -ForegroundColor Gray
    Write-Host "  Remove:      schtasks /delete /tn $TaskName /f" -ForegroundColor Gray
    Write-Host "  Or use:      .\setup_scheduler.ps1 -Remove" -ForegroundColor Gray
} catch {
    Write-Host "Failed to create task: $_" -ForegroundColor Red
}
