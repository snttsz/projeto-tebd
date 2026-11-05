param([string]$Destino)
$ErrorActionPreference = 'Stop'
$projetoRaiz = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $Destino) {
    $Destino = Join-Path $projetoRaiz ('output/Ciclo_Urbano_06-11-2026_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.zip')
}
$destinoCompleto = [System.IO.Path]::GetFullPath($Destino)
if (Test-Path -LiteralPath $destinoCompleto) { throw 'O arquivo de destino já existe. Use outro nome para preservar a entrega anterior.' }
$finalDir = Join-Path $projetoRaiz 'docs/entregas/final'
$manifesto = Get-Content -LiteralPath (Join-Path $finalDir 'manifesto_dashboards.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifesto.status -ne 'concluido') { throw 'A geração dos dashboards não está concluída.' }
foreach ($registro in $manifesto.sha256.PSObject.Properties) {
    $arquivo = Join-Path $finalDir $registro.Name
    $atual = (Get-FileHash -LiteralPath $arquivo -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($atual -ne $registro.Value) { throw "Artefato alterado após geração: $($registro.Name)" }
}
foreach ($registro in $manifesto.fontes_sha256.PSObject.Properties) {
    $arquivo = Join-Path $projetoRaiz $registro.Name
    $atual = (Get-FileHash -LiteralPath $arquivo -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($atual -ne $registro.Value) { throw "Fonte alterado após geração: $($registro.Name). Regenere o painel." }
}
$kmDir = Join-Path $projetoRaiz $manifesto.mineracao.pasta
$kmManifestoPath = Join-Path $kmDir 'manifesto.json'
if ((Get-FileHash -LiteralPath $kmManifestoPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifesto.mineracao.sha256_manifesto) {
    throw 'Manifesto da mineração diverge da geração dos dashboards.'
}
$kmManifesto = Get-Content -LiteralPath $kmManifestoPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($registro in $kmManifesto.sha256.PSObject.Properties) {
    $atual = (Get-FileHash -LiteralPath (Join-Path $kmDir $registro.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($atual -ne $registro.Value) { throw "Artefato da mineração alterado: $($registro.Name)" }
}
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($destinoCompleto)) | Out-Null
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$arquivos = @()
foreach ($nome in @('README.md', 'requirements.txt', '.env.example', '.gitignore')) {
    $arquivos += Get-Item -LiteralPath (Join-Path $projetoRaiz $nome)
}
foreach ($pasta in @('src', 'docs')) {
    $arquivos += Get-ChildItem -LiteralPath (Join-Path $projetoRaiz $pasta) -Recurse -File |
        Where-Object { $_.FullName -notmatch '[\\/](node_modules|__pycache__)[\\/]' -and $_.Extension -notin @('.pyc', '.tmp', '.log') }
}
$fluxo = [System.IO.File]::Open($destinoCompleto, [System.IO.FileMode]::CreateNew)
$zip = New-Object System.IO.Compression.ZipArchive($fluxo, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($arquivo in $arquivos) {
        $relativo = $arquivo.FullName.Substring($projetoRaiz.Length + 1).Replace('\', '/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $arquivo.FullName, ('Ciclo_Urbano/' + $relativo)) | Out-Null
    }
} finally { $zip.Dispose(); $fluxo.Dispose() }
$hashFinal = (Get-FileHash -LiteralPath $destinoCompleto -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText($destinoCompleto + '.sha256', $hashFinal + '  ' + [System.IO.Path]::GetFileName($destinoCompleto) + [Environment]::NewLine)
Write-Output "Pacote: $destinoCompleto"
Write-Output "Arquivos: $($arquivos.Count)"
Write-Output "SHA-256: $hashFinal"
