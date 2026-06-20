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
    $bgBrush = New-LinearBrush $outer ([System.Drawing.Color]::FromArgb(17,17,17)) ([System.Drawing.Color]::FromArgb(5,5,5)) 45
    $Graphics.FillPath($bgBrush, $outerPath)

    $accentPath = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $accentBrush = New-LinearBrush $outer ([System.Drawing.Color]::FromArgb(255,241,184)) ([System.Drawing.Color]::FromArgb(154,107,18)) 55
    $accentPen = [System.Drawing.Pen]::new([System.Drawing.Color]::White, 82*$scale)
    $accentPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $accentPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $Graphics.DrawLine($accentPen, $X + 352*$scale, $Y + 286*$scale, $X + 672*$scale, $Y + 286*$scale)
    $Graphics.DrawLine($accentPen, $X + 352*$scale, $Y + 738*$scale, $X + 672*$scale, $Y + 738*$scale)

    $whitePen = [System.Drawing.Pen]::new([System.Drawing.Color]::White, 126*$scale)
    $whitePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $whitePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $Graphics.DrawLine($whitePen, $X + 512*$scale, $Y + 322*$scale, $X + 512*$scale, $Y + 702*$scale)

    $thinAccentPen = [System.Drawing.Pen]::new($accentBrush, 26*$scale)
    $thinAccentPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $thinAccentPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $Graphics.DrawLine($thinAccentPen, $X + 512*$scale, $Y + 334*$scale, $X + 512*$scale, $Y + 690*$scale)

    $gold = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(212,175,55))
    $paleGold = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255,241,184))
    $Graphics.FillEllipse($gold, $X + (716-32)*$scale, $Y + (374-32)*$scale, 64*$scale, 64*$scale)
    $Graphics.FillEllipse($paleGold, $X + (760-22)*$scale, $Y + (512-22)*$scale, 44*$scale, 44*$scale)
    $Graphics.FillEllipse($gold, $X + (716-32)*$scale, $Y + (650-32)*$scale, 64*$scale, 64*$scale)

    $nodePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255,241,184), 18*$scale)
    $nodePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $nodePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $Graphics.DrawArc($nodePen, $X + 668*$scale, $Y + 374*$scale, 184*$scale, 276*$scale, -70, 140)
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

    $dark = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(17,17,17))
    $goldText = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(154,107,18))
    $line = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(229,231,235), 10)
    $accent = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(212,175,55), 10)
    $font = [System.Drawing.Font]::new("Segoe UI", 176, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $subFont = [System.Drawing.Font]::new("Segoe UI", 72, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $graphics.DrawString("Invoxia", $font, $dark, [System.Drawing.PointF]::new(744, 190))
    $graphics.DrawString("AI ASSISTANT", $subFont, $goldText, [System.Drawing.PointF]::new(754, 415))
    $graphics.DrawLine($line, 754, 556, 1374, 556)
    $graphics.DrawLine($accent, 754, 556, 1004, 556)

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
