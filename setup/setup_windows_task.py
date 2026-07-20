#!/usr/bin/env python
"""
Setup Windows Task Scheduler for hourly AQI collection.
Run this script with Administrator privileges.
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_task_scheduler():
    """Create Windows Task Scheduler task for hourly AQI collection."""
    
    # Get current directory
    project_root = Path(__file__).parent.absolute()
    python_exe = sys.executable
    collector_script = project_root / "collector.py"
    log_file = project_root / "data-pipeline" / "logs" / "task_scheduler.log"
    
    print(f"\n{'='*70}")
    print("Windows Task Scheduler Setup for VayuGuard AQI Collection")
    print(f"{'='*70}\n")
    
    print(f"Project Root: {project_root}")
    print(f"Python Executable: {python_exe}")
    print(f"Collector Script: {collector_script}")
    print(f"Log File: {log_file}\n")
    
    # Task XML definition
    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-06-15T00:00:00Z</Date>
    <Author>VayuGuard</Author>
    <Description>Hourly AQI data collection from WAQI API</Description>
    <URI>\\VayuGuard\\AQI_Collection</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <Repetition>
        <Interval>PT1H</Interval>
        <Duration>P999Y</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2026-06-15T00:00:00Z</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-21-3623811015-3361044348-30300820-1001</UserId>
      <LogonType>Interactive</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <NetworkSettings>
      <EnableNetworkProfile>false</EnableNetworkProfile>
    </NetworkSettings>
    <IdleSettings>
      <Duration>PT5M</Duration>
      <WaitTimeout>PT1H</WaitTimeout>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT5M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{python_exe}"</Command>
      <Arguments>"{collector_script}"</Arguments>
      <WorkingDirectory>{project_root}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''
    
    # Save task XML
    task_xml_file = project_root / "setup" / "vayuguard_aqi_collection.xml"
    task_xml_file.parent.mkdir(parents=True, exist_ok=True)
    with open(task_xml_file, 'w', encoding='utf-16') as f:
        f.write(task_xml)
    
    print(f"✅ Task XML created: {task_xml_file}\n")
    
    # Instructions
    print("="*70)
    print("INSTALLATION INSTRUCTIONS")
    print("="*70 + "\n")
    
    print("Method 1: Using PowerShell (Recommended)")
    print("-" * 70)
    print("1. Open PowerShell as Administrator")
    print("2. Run the following command:\n")
    print(f'   Register-ScheduledTask -Xml (Get-Content "{task_xml_file}" | Out-String) -TaskName "VayuGuard AQI Collection" -Force\n')
    
    print("Method 2: Using Task Scheduler GUI")
    print("-" * 70)
    print("1. Open Task Scheduler (taskschd.msc)")
    print("2. Right-click 'Task Scheduler Library' → 'New Folder...'")
    print("3. Name the folder 'VayuGuard'")
    print("4. Right-click the new 'VayuGuard' folder → 'Create Task...'")
    print("5. Import the XML file above")
    print("6. Set trigger to 'Repeat every 1 hour'")
    print("7. Action: Python script → collector.py")
    print("8. Run with highest privileges: ✓\n")
    
    print("Method 3: Using Command Line")
    print("-" * 70)
    print("1. Open Command Prompt as Administrator")
    print(f'2. Run: schtasks /create /tn "VayuGuard\\AQI Collection" /tr "\'{python_exe}\' \'{collector_script}\'" /sc hourly /mo 1 /f\n')
    
    print("="*70)
    print("VERIFICATION")
    print("="*70 + "\n")
    
    print("To verify the task is working:")
    print("1. Open Task Scheduler (taskschd.msc)")
    print("2. Navigate to: Task Scheduler Library > VayuGuard")
    print("3. Look for 'AQI Collection' task")
    print("4. Check 'Last Run Result' (should be 'The task completed with an exit code (0).')")
    print("5. View logs: data-pipeline/logs/collector_YYYYMMDD.log\n")
    
    print("="*70)
    print("MANUAL TESTING")
    print("="*70 + "\n")
    
    print(f"To test the collection script manually:\n")
    print(f'   cd "{project_root}"')
    print(f'   RUN_ONCE=1 python collector.py\n')
    
    print("="*70)
    print("TROUBLESHOOTING")
    print("="*70 + "\n")
    
    print("If the task doesn't run:")
    print("1. Check that PostgreSQL is running and accessible")
    print("2. Verify WAQI_API_KEY is set in .env")
    print("3. Check Windows firewall allows the connection")
    print("4. Review log files in data-pipeline/logs/")
    print("5. Run manually with RUN_ONCE=1 to test connectivity\n")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    # Check if running as admin
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        import ctypes
        is_admin = ctypes.windll.shell.IsUserAnAdmin()
    
    if is_admin or '--skip-admin' in sys.argv:
        setup_task_scheduler()
    else:
        print("⚠️  This script should be run as Administrator")
        print("   Right-click this script and select 'Run as administrator'")
        print("\n   Or run: python setup_windows_task.py --skip-admin")
