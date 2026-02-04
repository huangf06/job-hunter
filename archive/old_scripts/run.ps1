# Job Hunter PowerShell Launcher
# ==============================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("scrape", "analyze", "generate", "apply", "daily", "stats", "help")]
    [string]$Command = "help",
    
    [string]$Platform = "linkedin",
    [string]$Search = "data scientist",
    [string]$Location = "Netherlands",
    [string]$JobId = "",
    [string]$Company = "",
    [switch]$NoDryRun,
    [int]$MaxJobs = 25
)

$ErrorActionPreference = "Stop"

# 设置 Python 路径
$PYTHON = "C:\Users\huang\AppData\Local\Programs\Python\Python312\python.exe"
$SCRIPT_DIR = $PSScriptRoot

function Show-Help {
    Write-Host @"
Job Hunter - Automated Job Search & Apply System
================================================

Commands:
  scrape    爬取职位
  analyze   分析职位匹配度
  generate  生成定制简历
  apply     执行投递
  daily     运行每日完整流程
  stats     查看统计

Usage Examples:
  .\run.ps1 scrape -Platform linkedin -Search "data scientist"
  .\run.ps1 analyze
  .\run.ps1 generate -Company "Picnic"
  .\run.ps1 apply                    # 预览模式
  .\run.ps1 apply -NoDryRun          # 实际投递
  .\run.ps1 daily                    # 每日完整流程
  .\run.ps1 stats                    # 查看统计
"@
}

function Run-Command {
    param([string]$CmdArgs)
    
    Write-Host "Executing: $PYTHON $CmdArgs" -ForegroundColor Cyan
    & $PYTHON $CmdArgs.Split(" ")
}

# 主逻辑
switch ($Command) {
    "help" { Show-Help }
    
    "scrape" {
        if ($Platform -eq "all") {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py scrape --platform all"
        } else {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py scrape --platform $Platform --search `"$Search`" --location $Location --max-jobs $MaxJobs"
        }
    }
    
    "analyze" {
        Run-Command "$SCRIPT_DIR\job_hunter_cli.py analyze"
    }
    
    "generate" {
        if ($JobId) {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py generate --job-id $JobId"
        } elseif ($Company) {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py generate --company `"$Company`""
        } else {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py generate"
        }
    }
    
    "apply" {
        if ($NoDryRun) {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py apply --no-dry-run"
        } else {
            Run-Command "$SCRIPT_DIR\job_hunter_cli.py apply"
        }
    }
    
    "daily" {
        Run-Command "$SCRIPT_DIR\job_hunter_cli.py daily"
    }
    
    "stats" {
        Run-Command "$SCRIPT_DIR\job_hunter_cli.py stats"
    }
}
