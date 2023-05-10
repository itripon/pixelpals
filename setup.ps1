$ErrorActionPreference = 'Stop'
$settings = Get-Content -Path settings.json | ConvertFrom-Json
$cwd = (get-location).path

function check_sources {
    param (
        # Carla local source path
        [string]
        $CarlaPath,
        # ScenarioRunner local source path
        [string]
        $ScenarioRunnnerPath
    )
    return (Test-Path $CarlaPath) -and (Test-Path $ScenarioRunnnerPath)
}

function cleanup {
    param (
        # Carla download destination
        [string]
        $carla_destination,
        # ScenarioRunner download destination
        [string]
        $scenario_runner_destination,
        [string]
        # CSV with the files we need to download
        $temp_files_to_download_csv
    )
    if (Test-Path $carla_destination) {
        Remove-Item -Force $carla_destination
    }
    if (Test-Path $scenario_runner_destination) {
        Remove-Item -Force $scenario_runner_destination
    }
    if (Test-Path $temp_files_to_download_csv) {
        Remove-Item -Force $temp_files_to_download_csv
    }
}
# Check if the source files are available if not download them
if (-not(check_sources $settings.carla_local $settings.scenario_runner_local)) {
    # Delete old files if any
    cleanup $settings.carla_destination $settings.scenario_runner_destination $settings.temp_files_to_download_csv
    if (Test-Path $settings.carla_local) {
        Remove-Item -Force -Recurse $settings.carla_local
    }
    if (Test-Path $settings.scenario_runner_local) {
        Remove-Item -Force -Recurse $settings.scenario_runner_local
    }

    # Download files
    foreach ($row in $settings.files_to_download) {
        Write-Output("Downloading file $row.Uri")
        Invoke-WebRequest -Uri $row.Uri -OutFile $row.OutFile
    }

    # Extract from archives
    Write-Output("Extracting from acrhives")
    Expand-Archive -Path $settings.carla_destination -DestinationPath $settings.carla_local
    Expand-Archive -Path $settings.scenario_runner_destination -DestinationPath $settings.scenario_runner_local

    # Cleanup temp and downloaded resources
    Write-Output("Performing cleanup")
    cleanup $settings.carla_destination $settings.scenario_runner_destination $settings.temp_files_to_download_csv
}



# Check if python viratul environment is created, oterwise activate it and install requirements
if (-not(Test-Path .venv)) {
    Write-Output("Setting up Python virtual environment and installing requirements")
    $create_venv_command = $settings.python37path + " -m venv .venv"
    $scenario_runner_requirements = $settings.pip_install_requirements + $cwd + $settings.sep + $settings.scenario_runner_local + $settings.sep + $settings.scenario_runner_path + $settings.sep + $settings.requirements_file
    $carla_requirements = $settings.pip_install_requirements + $cwd + $settings.sep + $settings.carla_local + $settings.sep + $settings.carla_python_api_requirements_path + $settings.sep + $settings.requirements_file
    $install_carla_package = $settings.pip_install + " carla"
    Invoke-Expression $create_venv_command
    .venv/Scripts/activate.ps1
    Invoke-Expression $install_carla_package
    Invoke-Expression $scenario_runner_requirements
    Invoke-Expression $carla_requirements
}
