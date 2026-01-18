@echo off
REM ================================================================
REM Green Corridor System - Quick Start Menu
REM Emergency Vehicle Routing Research System
REM ================================================================

:menu
cls
echo ================================================================
echo    GREEN CORRIDOR SYSTEM - EMERGENCY VEHICLE ROUTING
echo ================================================================
echo.
echo 1. Test Single Algorithm
echo 2. Run Batch Experiments (Full Research Data)
echo 3. Analyze Existing Results
echo 4. Network Statistics
echo 5. Generate Traffic Scenarios
echo 6. Verify Installation
echo 7. View Documentation
echo 8. Install/Update Dependencies
echo 9. Exit
echo.
echo ================================================================
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto test_algorithm
if "%choice%"=="2" goto batch_experiments
if "%choice%"=="3" goto analyze
if "%choice%"=="4" goto network_stats
if "%choice%"=="5" goto generate_traffic
if "%choice%"=="6" goto verify
if "%choice%"=="7" goto docs
if "%choice%"=="8" goto install_deps
if "%choice%"=="9" goto end

echo Invalid choice. Please try again.
pause
goto menu

:test_algorithm
cls
echo ================================================================
echo TEST SINGLE ALGORITHM
echo ================================================================
echo.
echo Available algorithms:
echo 1. Adaptive A* (adaptive_astar.py) - Dynamic weights
echo 2. Standard A* (standard_astar.py) - Fixed weights (0.6/0.4)
echo 3. Dijkstra (dijkstra.py) - Distance-only
echo 4. CH (ch.py) - Contraction Hierarchies
echo 5. CHWrapper (chwrapper.py) - Hybrid approach
echo 6. ALT (alt.py) - A* with landmarks
echo.
set /p algo_choice="Select algorithm (1-6): "

if "%algo_choice%"=="1" set algo=adaptive_astar.py
if "%algo_choice%"=="2" set algo=standard_astar.py
if "%algo_choice%"=="3" set algo=dijkstra.py
if "%algo_choice%"=="4" set algo=ch.py
if "%algo_choice%"=="5" set algo=chwrapper.py
if "%algo_choice%"=="6" set algo=alt.py

echo.
echo Test Routes:
echo 1. Route 1: 290640275#1 to 323470681#1 (2.73 km, 6 signals)
echo 2. Route 2: -1213264717 to 23542229#4 (3.29 km, 1 signal)
echo 3. Route 3: -1213264717 to -1213264717 (2.50 km, 2 signals)
echo.
set /p route_choice="Select route (1-3): "

if "%route_choice%"=="1" (
    set start=290640275#1
    set goal=323470681#1
)
if "%route_choice%"=="2" (
    set start=-1213264717
    set goal=23542229#4
)
if "%route_choice%"=="3" (
    set start=-1213264717
    set goal=-1213264717
)

echo.
echo Emergency Severity (Adaptive A* only):
echo 1. CRITICAL (max urgency, weight shift: +15%%)
echo 2. HIGH (moderate urgency, weight shift: +8%%)
echo 3. MEDIUM (normal, weight shift: +5%%)
echo.
set /p severity_choice="Select severity (1-3): "

if "%severity_choice%"=="1" set severity=CRITICAL
if "%severity_choice%"=="2" set severity=HIGH
if "%severity_choice%"=="3" set severity=MEDIUM

echo.
echo Traffic Levels:
echo 1. low (0.07 veh/km, 200 vehicles)
echo 2. moderate (0.18 veh/km, 500 vehicles)
echo 3. high (0.35 veh/km, 1000 vehicles)
echo.
set /p traffic_choice="Select traffic (1-3): "

if "%traffic_choice%"=="1" set traffic=low
if "%traffic_choice%"=="2" set traffic=moderate
if "%traffic_choice%"=="3" set traffic=high

cls
echo ================================================================
echo RUNNING TEST
echo ================================================================
echo Algorithm: %algo%
echo Route: %start% to %goal%
echo Severity: %severity%
echo Traffic: %traffic%
echo ================================================================
echo.

cd src\algorithms
python %algo% --start "%start%" --goal "%goal%" --severity %severity% --traffic %traffic%
cd ..\..

echo.
echo ================================================================
echo Test complete!
echo ================================================================
pause
goto menu

:batch_experiments
cls
echo ================================================================
echo BATCH EXPERIMENTS (RESEARCH PAPER DATA)
echo ================================================================
echo.
echo Experiment Matrix:
echo - 6 algorithms (1 proposed + 5 baselines)
echo - 3 traffic levels (low, moderate, high)
echo - 3 test routes
echo - 3 severities (Adaptive A* only)
echo.
echo Total: 96 configurations
echo ================================================================
echo.
echo Estimated time: 8-12 hours (recommend overnight run)
echo.
set /p runs="Enter number of runs per configuration (1-10, default=5): "
if "%runs%"=="" set runs=5

echo.
set /p output_name="Output filename (default=full_results): "
if "%output_name%"=="" set output_name=full_results

echo.
echo Configuration:
echo - Runs per config: %runs%
echo - Output: results\%output_name%.json
echo - Report: results\%output_name%_summary.md
echo.
set /p confirm="Start batch experiments? (y/n): "
if /i "%confirm%" NEQ "y" goto menu

cls
echo ================================================================
echo RUNNING BATCH EXPERIMENTS
echo ================================================================
echo.

cd src\experiments
python batch_runner.py --runs %runs% --output ..\..\results\%output_name%.json --report ..\..\results\%output_name%_summary.md
cd ..\..

echo.
echo ================================================================
echo Batch experiments complete!
echo Results saved to: results\%output_name%.json
echo.
echo Next step: Analyze results (Option 3 from main menu)
echo ================================================================
pause
goto menu

:analyze
cls
echo ================================================================
echo ANALYZE EXPERIMENT RESULTS
echo ================================================================
echo.
echo Available result files:
dir /b results\*.json 2>nul
echo.
set /p results_file="Enter results filename (e.g., full_results.json): "

if not exist "results\%results_file%" (
    echo Error: File not found: results\%results_file%
    pause
    goto menu
)

set base_name=%results_file:.json=%

echo.
echo Generating analysis:
echo - Markdown report: results\%base_name%_analysis.md
echo - LaTeX table: results\%base_name%_table.tex
echo - CSV export: results\%base_name%_data.csv
echo.

cd src\experiments
python analyzer.py ..\..\results\%results_file% --markdown ..\..\results\%base_name%_analysis.md --latex ..\..\results\%base_name%_table.tex --csv ..\..\results\%base_name%_data.csv
cd ..\..

echo.
echo ================================================================
echo Analysis complete!
echo.
echo Generated files:
echo - results\%base_name%_analysis.md    (Statistical report)
echo - results\%base_name%_table.tex      (LaTeX table for paper)
echo - results\%base_name%_data.csv       (Raw data export)
echo ================================================================
pause
goto menu

:network_stats
cls
echo ================================================================
echo NETWORK STATISTICS
echo ================================================================
echo.
cd src\utils
python network_stats.py
cd ..\..
echo.
echo ================================================================
pause
goto menu

:generate_traffic
cls
echo ================================================================
echo GENERATE TRAFFIC SCENARIOS
echo ================================================================
echo.
echo This will generate traffic files for low/moderate/high scenarios
echo.
set /p confirm="Continue? (y/n): "
if /i "%confirm%" NEQ "y" goto menu

cd src\utils
python generate_traffic.py
cd ..\..

echo.
echo ================================================================
echo Traffic scenarios generated!
echo ================================================================
pause
goto menu

:verify
cls
echo ================================================================
echo VERIFY INSTALLATION
echo ================================================================
echo.
echo Checking dependencies...
echo.

REM Check Python
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.11 or higher
) else (
    echo [OK] Python found
)

REM Check SUMO
sumo --version 2>nul
if errorlevel 1 (
    echo [ERROR] SUMO not found!
    echo Please install SUMO 1.25.0 or higher
    echo Download from: https://eclipse.dev/sumo/
) else (
    echo [OK] SUMO found
)

REM Check Python packages
echo.
echo Checking Python packages...
python -c "import sumolib" 2>nul
if errorlevel 1 (
    echo [ERROR] sumolib not found
) else (
    echo [OK] sumolib
)

python -c "import traci" 2>nul
if errorlevel 1 (
    echo [ERROR] traci not found
) else (
    echo [OK] traci
)

python -c "import scipy" 2>nul
if errorlevel 1 (
    echo [ERROR] scipy not found - run option 8 to install
) else (
    echo [OK] scipy
)

python -c "import numpy" 2>nul
if errorlevel 1 (
    echo [ERROR] numpy not found - run option 8 to install
) else (
    echo [OK] numpy
)

REM Check network file
echo.
echo Checking network files...
if exist "data\bangalore.net.xml" (
    echo [OK] bangalore.net.xml found
) else (
    echo [ERROR] bangalore.net.xml not found in data\ folder
)

echo.
echo ================================================================
echo Verification complete!
echo ================================================================
pause
goto menu

:docs
cls
echo ================================================================
echo DOCUMENTATION
echo ================================================================
echo.
echo Available documentation:
echo.
echo 1. README.md                        - Project overview
echo 2. docs\PAPER_DRAFT_SECTIONS.md    - Research paper draft
echo 3. requirements.txt                - Dependency list
echo.
set /p doc_choice="Enter number to open (1-3), or press Enter to return: "

if "%doc_choice%"=="1" start README.md
if "%doc_choice%"=="2" start docs\PAPER_DRAFT_SECTIONS.md
if "%doc_choice%"=="3" start requirements.txt

goto menu

:install_deps
cls
echo ================================================================
echo INSTALL/UPDATE DEPENDENCIES
echo ================================================================
echo.
echo This will install/update required Python packages:
echo - scipy (statistical analysis)
echo - numpy (numerical computing)
echo.
set /p confirm="Continue? (y/n): "
if /i "%confirm%" NEQ "y" goto menu

pip install --upgrade scipy numpy

echo.
echo ================================================================
echo Dependencies installed/updated!
echo ================================================================
pause
goto menu

:end
cls
echo ================================================================
echo    GREEN CORRIDOR SYSTEM
echo    Emergency Vehicle Routing Research
echo ================================================================
echo.
echo Thank you for using the Green Corridor System!
echo.
echo For questions or issues:
echo - Check README.md
echo - Review docs\PAPER_DRAFT_SECTIONS.md
echo.
echo Research Paper: Adaptive A* with Multi-Phase Preemption
echo Network: Bangalore (532,847 edges, 1,247 signals)
echo.
echo Good luck with your research!
echo ================================================================
pause
exit
