# Como executar no WSL Ubuntu - Windows 11

## 1. Instalar WSL e Ubuntu

Abra **PowerShell como Administrador** e execute:

```powershell
wsl --install -d Ubuntu
```

Reinicie o Windows se solicitado. Abra o aplicativo **Ubuntu** pelo menu Iniciar e conclua a criação de usuário/senha Linux.

Para verificar:

```powershell
wsl --status
wsl -l -v
```

## 2. Colocar o ZIP em uma pasta do Windows

Exemplo:

```text
C:\Users\SEU_USUARIO\Downloads\MapBiomas_Heatwaves_Accuracy_Reproducibility.zip
```

No WSL, a unidade `C:` aparece em `/mnt/c`.

```bash
cd ~
mkdir -p mapbiomas_accuracy
cd mapbiomas_accuracy
cp /mnt/c/Users/SEU_USUARIO/Downloads/MapBiomas_Heatwaves_Accuracy_Reproducibility.zip .
unzip MapBiomas_Heatwaves_Accuracy_Reproducibility.zip
cd MapBiomas_Heatwaves_Accuracy_Reproducibility
```

**Recomendação:** rode a análise dentro do filesystem Linux (`~/...`), e não diretamente em `/mnt/c/...`, porque o acesso a muitos arquivos pequenos costuma ser mais rápido no filesystem do WSL.

## 3. Instalar o ambiente

```bash
chmod +x setup_wsl.sh run_all.sh
./setup_wsl.sh
```

O script pede sua senha Ubuntu para instalar `python3`, `venv`, `pip` e `unzip`, cria `.venv` e instala versões fixadas das bibliotecas Python.

Depois:

```bash
source .venv/bin/activate
```

## 4. Reproduzir todas as análises e o fact-sheet

```bash
./run_all.sh
```

Ou:

```bash
make all
```

Tempo esperado: depende do computador, mas o processamento é local e não consulta o Earth Engine.

## 5. Resultados

```text
outputs/generated/heatwaves/
outputs/generated/tmax/
outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet.pdf
```

Para abrir o diretório de saída no Windows Explorer:

```bash
explorer.exe outputs/generated/report
```

## 6. Verificação numérica

```bash
make verify
```

O teste confirma, entre outros, os valores aproximados:

- V2 anual `heatwave_days`: r = 0,7125; RMSE = 12,2333 dias.
- V1 anual: r = 0,1680; RMSE = 16,2031 dias.
- Brasília Tmax diária: RMSE = 1,3281 °C.
- Goiânia Tmax diária: bias = -2,9187 °C.
- Porto Alegre: F1 dia > TX90 = 0,7562.
- Manaus: recall para dias pertencentes a sequências WSDI = 0,8173.

## 7. Recriar apenas uma parte

Validação V1 x V2:

```bash
python src/analyze_heatwaves.py \
  --annual data/gee_exports/heatwaves/HW_validation_annual_urban_centroids_1985_2025.csv \
  --monthly data/gee_exports/heatwaves/HW_validation_monthly_urban_centroids_1985_2025.csv \
  --centroids data/reference/HW_validation_urban_centroids.csv \
  --outdir outputs/generated/heatwaves
```

Tmax:

```bash
python src/analyze_tmax.py \
  --station data/stations/tmax/Maximas_capitais.csv \
  --era5-dir data/gee_exports/era5_tmax \
  --outdir outputs/generated/tmax
```

Fact-sheet:

```bash
python src/generate_factsheet.py \
  --heatwave-out outputs/generated/heatwaves \
  --tmax-out outputs/generated/tmax \
  --centroids data/reference/HW_validation_urban_centroids.csv \
  --outfile outputs/generated/report/MapBiomas_Atmosfera_Heatwaves_Accuracy_Factsheet.pdf
```

## 8. Problemas comuns

### `python3-venv` ausente

```bash
sudo apt update
sudo apt install python3-venv
```

### Erro ao instalar SciPy

Normalmente o wheel é instalado automaticamente. Se a distribuição Ubuntu/Python for muito diferente, tente:

```bash
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### PDF não abre diretamente no WSL

```bash
explorer.exe outputs/generated/report
```

ou copie para o Windows:

```bash
cp outputs/generated/report/*.pdf /mnt/c/Users/SEU_USUARIO/Downloads/
```
