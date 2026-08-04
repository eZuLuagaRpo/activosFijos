@echo off
REM ===========================================================================
REM  build.bat - Empaqueta el RPA de Activos Fijos en un ejecutable (.exe)
REM  con PyInstaller.
REM
REM  USO:
REM    1) Abre esta carpeta en una terminal (cmd).
REM    2) Activa el entorno virtual que tiene las dependencias, por ejemplo:
REM         ..\venv\Scripts\activate
REM    3) Ejecuta:  build.bat
REM
REM  RESULTADO: se crea la carpeta  dist\RPA_Activos_Fijos\  con el .exe y todo
REM  lo necesario. Esa carpeta COMPLETA es la que se le entrega a la usuaria.
REM
REM  NOTA: se usa modo carpeta (--onedir), que es MAS ESTABLE con Selenium y con
REM  los assets. Si se prefiere un unico archivo, ver la variante --onefile mas
REM  abajo (comentada), pero arranca mas lento y el antivirus a veces la marca.
REM ===========================================================================

echo.
echo === Empaquetando RPA Activos Fijos (modo carpeta --onedir) ===
echo.

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --name "RPA_Activos_Fijos" ^
  --icon "assets\icon.ico" ^
  --add-data "assets;assets" ^
  --add-data "transformacion\mapping;transformacion\mapping" ^
  --hidden-import customtkinter ^
  --hidden-import PIL ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import pandas ^
  --hidden-import openpyxl ^
  --hidden-import selenium ^
  --hidden-import an0016001_appian_flow ^
  --collect-all customtkinter ^
  --collect-all an0016001_appian_flow ^
  app.py

echo.
echo === Listo. Revisa la carpeta dist\RPA_Activos_Fijos ===
echo.
pause

REM ---------------------------------------------------------------------------
REM  VARIANTE UN SOLO ARCHIVO (--onefile). Descomenta para usarla en vez de la
REM  de arriba. Arranca mas lento y algunos antivirus corporativos la marcan.
REM ---------------------------------------------------------------------------
REM pyinstaller --noconfirm --clean --windowed --onefile ^
REM   --name "RPA_Activos_Fijos" --icon "assets\icon.ico" ^
REM   --add-data "assets;assets" ^
REM   --add-data "transformacion\mapping;transformacion\mapping" ^
REM   --collect-all customtkinter --collect-all an0016001_appian_flow app.py
