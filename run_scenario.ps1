$ErrorActionPreference = 'Stop'
$settings = Get-Content -Path settings.json | ConvertFrom-Json
$cwd = (get-location).path

function check_if_ening_is_running {
    param(
        # Carla engine exe path
        [string]
        $process_name
    )
    $process = Get-Process -Name $process_name -ErrorAction SilentlyContinue
    return -not($process -eq $null)
}

# Activte virtual environment
.venv/Scripts/activate.ps1

# Add to PYTHONPATH
$current_path = "$env:PYTHONPATH"
$to_add = $cwd + $settings.sep + $settings.carla_local + $settings.sep + $settings.carla_python_api_path + ";" + $cwd + $settings.sep + $settings.scenario_runner_local + $settings.sep + $settings.scenario_runner_path + ";"
$env:PYTHONPATH += $to_add

# Start Carla engine  if it's not already running and wait 30 seconds
$carla_engine_path = $cwd + $settings.sep + $settings.carla_local + $settings.sep + $settings.carla_engine_path + $settings.sep + $settings.carla_process + ".exe"

if (-not(check_if_ening_is_running $settings.carla_process)) {
    Write-Output("Starting CarlaUE4 engine")
    Invoke-Expression $carla_engine_path
    Start-Sleep -Seconds 20
}

# Start scenario
Write-Output("Starting scenario(s)")
$scenario_command = "python " + $cwd + $settings.sep + $settings.scenario_runner_local + $settings.sep + $settings.scenario_runner_path + $settings.sep + $settings.scenario_runner + " " + $settings.scenario_to_execute
$scenario_command
Invoke-Expression $scenario_command
Invoke-Expression "python utils\image_combine.py"

# Stop Carla engine if it's running
if (check_if_ening_is_running $settings.carla_process) {
    Write-Output("Stopping CarlaUE4 engine")
    Stop-Process -Name $settings.carla_process_shipping
    Stop-Process -Name $settings.carla_process
    Start-Sleep -Seconds 10
}
$env:PYTHONPATH = $current_path
