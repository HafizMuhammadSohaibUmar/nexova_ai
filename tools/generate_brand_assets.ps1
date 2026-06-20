param(
    [string]$OutputDir = "nexova_ai/public/branding"
)

Add-Type -AssemblyName System.Drawing

$root = Resolve-Path "."
$out = Join-Path $root $OutputDir
New-Item -ItemType Directory -Force -Path $out | Out-Null

function New-LinearBrush {
    param(
        [System.Drawing.RectangleF]$Rect,
        [System.Drawing.Color]$Start,
        [System.Drawing.Color]$End,
        [float]$Angle = 45
    )
    return [System.Drawing.Drawing2D.LinearGradientBrush]::new($Rect, $Start, $End, $Angle)
}

function Set-Quality {
    param([System.Drawing.Graphics]$Graphics)
    $Graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $Graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $Graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $Graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
}

function Add-RoundedRectangle {
    param(
        [System.Drawing.Drawing2D.GraphicsPath]$Path,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )
    $diameter = $Radius * 2
    $Path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $Path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $Path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $Path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $Path.CloseFigure()
}

function Draw-Mark {
    param(
        [System.Drawing.Graphics]$Graphics,
        [float]$X,
        [float]$Y,
        [float]$Size
    )

    $scale = $Size / 1024
    $outer = [System.Drawing.RectangleF]::new($X + 96*$scale, $Y + 96*$scale, 832*$scale, 832*$scale)
    $outerPath = [System.Drawing.Drawing2D.GraphicsPath]::new()
    Add-RoundedRectangle $outerPath $outer.X $outer.Y $outer.Width $outer.Height (220*$scale)
    $bgBrush = New-LinearBrush $outer ([System.Drawing.Color]::FromArgb(7,17,31)) ([System.Drawing.Color]::FromArgb(6,21,27)) 45
    $Graphics.FillPath($bgBrush, $outerPath)

    $accentPath = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $inner = [System.Drawing.RectangleF]::new($X + 216*$scale, $Y + 258*$scale, 592*$scale, 508*$scale)
    Add-RoundedRectangle $accentPath $inner.X $inner.Y $inner.Width $inner.Height (106*$scale)
    $accentBrush = New-LinearBrush $inner ([System.Drawing.Color]::FromArgb(30,231,255)) ([System.Drawing.Color]::FromArgb(251,191,36)) 45
    $accentPen = [System.Drawing.Pen]::new($accentBrush, 42*$scale)
    $Graphics.DrawPath($accentPen, $accentPath)

    $whitePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(248,250,252), 58*$scale)
    $whitePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $whitePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $Graphics.DrawLine($whitePen, $X + 350*$scale, $Y + 378*$scale, $X + 674*$scale, $Y + 378*$scale)
    $Graphics.DrawLine($whitePen, $X + 350*$scale, $Y + 512*$scale, $X + 588*$scale, $Y + 512*$scale)
    $Graphics.DrawLine($whitePen, $X + 350*$scale, $Y + 646*$scale, $X + 674*$scale, $Y + 646*$scale)

    $cyan = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(30,231,255))
    $green = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(52,211,153))
    $Graphics.FillEllipse($cyan, $X + (684-42)*$scale, $Y + (512-42)*$scale, 84*$scale, 84*$scale)
    $Graphics.FillEllipse($green, $X + (744-24)*$scale, $Y + (512-24)*$scale, 48*$scale, 48*$scale)
}

function Save-MarkPng {
    param([int]$Size, [string]$Path)
    $bitmap = [System.Drawing.Bitmap]::new($Size, $Size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    Set-Quality $graphics
    $graphics.Clear([System.Drawing.Color]::Transparent)
    Draw-Mark $graphics 0 0 $Size
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

function Save-LogoPng {
    param([int]$Width, [int]$Height, [string]$Path)
    $bitmap = [System.Drawing.Bitmap]::new($Width, $Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    Set-Quality $graphics
    $graphics.Clear([System.Drawing.Color]::White)
    Draw-Mark $graphics 60 70 620

    $dark = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(7,17,31))
    $teal = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(15,118,110))
    $line = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(217,226,232), 10)
    $accent = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(52,211,153), 10)
    $font = [System.Drawing.Font]::new("Segoe UI", 176, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $subFont = [System.Drawing.Font]::new("Segoe UI", 72, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $graphics.DrawString("Invoxia", $font, $dark, [System.Drawing.PointF]::new(730, 190))
    $graphics.DrawString("AI ASSISTANT", $subFont, $teal, [System.Drawing.PointF]::new(740, 415))
    $graphics.DrawLine($line, 735, 552, 1350, 552)
    $graphics.DrawLine($accent, 735, 552, 970, 552)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

Save-LogoPng 2400 760 (Join-Path $out "invoxia-logo-2400x760.png")
Save-MarkPng 1024 (Join-Path $out "invoxia-mark-1024.png")
Save-MarkPng 512 (Join-Path $out "invoxia-favicon-512.png")
Save-MarkPng 256 (Join-Path $out "invoxia-favicon-256.png")
Save-MarkPng 64 (Join-Path $out "invoxia-favicon-64.png")

Write-Host "Brand assets generated in $out"
