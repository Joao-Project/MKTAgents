Add-Type -AssemblyName System.Drawing
$pasta = $PSScriptRoot
Get-ChildItem -LiteralPath $pasta -Filter 'post-*.png' | ForEach-Object {
    $caminho = $_.FullName
    $origem = [System.Drawing.Image]::FromFile($caminho)
    try {
        if ($origem.Width -ne $origem.Height) { throw "Imagem nao quadrada: $caminho" }
        if ($origem.Width -eq 1080) { return }
        $saida = [System.Drawing.Bitmap]::new(1080, 1080)
        try {
            $grafico = [System.Drawing.Graphics]::FromImage($saida)
            try {
                $grafico.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $grafico.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $grafico.DrawImage($origem, 0, 0, 1080, 1080)
            } finally { $grafico.Dispose() }
            $origem.Dispose()
            $saida.Save($caminho, [System.Drawing.Imaging.ImageFormat]::Png)
        } finally { $saida.Dispose() }
    } finally { $origem.Dispose() }
}
