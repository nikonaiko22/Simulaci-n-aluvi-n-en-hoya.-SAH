using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Media;
using System;
using System.Linq;
using System.Collections.Generic;

namespace SAH.UI.Controls
{
    public partial class ChartControl : UserControl
    {
        private Canvas? _canvas;
        private double[] _volumes = Array.Empty<double>();
        private double[] _flows = Array.Empty<double>();
        private bool _useBars = true; // barras vs línea
        private bool _showVolume = true; // mostrar volumen (true) o caudal (false)

        private readonly IBrush _lineBrush = SolidColorBrush.Parse("#0B5F50");
        private readonly IBrush _barBrush = SolidColorBrush.Parse("#19D0A8");
        private readonly IBrush _textBrush = SolidColorBrush.Parse("#3F6060");

        public ChartControl()
        {
            InitializeComponent();
            _canvas = this.FindControl<Canvas>("PlotCanvas");
            // re-render on size changed
            this.AttachedToVisualTree += (_, __) => { if (_canvas != null) _canvas.SizeChanged += (_, __) => Render(); };
        }

        public void SetData(double[] volumes, double[] flows)
        {
            _volumes = volumes ?? Array.Empty<double>();
            _flows = flows ?? Array.Empty<double>();
            Render();
        }

        public void SetMode(bool useBars, bool showVolume)
        {
            _useBars = useBars;
            _showVolume = showVolume;
            Render();
        }

        private void Render()
        {
            if (_canvas == null) return;
            _canvas.Children.Clear();

            var data = _showVolume ? _volumes : _flows;
            if (data == null || data.Length == 0) return;

            double width = Math.Max(100, _canvas.Bounds.Width);
            double height = Math.Max(80, _canvas.Bounds.Height);
            double marginLeft = 48;
            double marginBottom = 32;
            double marginTop = 12;
            double plotW = Math.Max(10, width - marginLeft - 12);
            double plotH = Math.Max(10, height - marginTop - marginBottom);

            int n = data.Length;
            double maxVal = data.Max();
            if (maxVal <= 0) maxVal = 1;

            // draw axes lines
            var axisBrush = SolidColorBrush.Parse("#DDEFEF");
            var yAxis = new Line
            {
                StartPoint = new Point(marginLeft, marginTop),
                EndPoint = new Point(marginLeft, marginTop + plotH),
                Stroke = axisBrush,
                StrokeThickness = 1
            };
            var xAxis = new Line
            {
                StartPoint = new Point(marginLeft, marginTop + plotH),
                EndPoint = new Point(marginLeft + plotW, marginTop + plotH),
                Stroke = axisBrush,
                StrokeThickness = 1
            };
            _canvas.Children.Add(yAxis);
            _canvas.Children.Add(xAxis);

            // Y axis labels (3 ticks)
            for (int t = 0; t <= 3; t++)
            {
                double frac = t / 3.0;
                double y = marginTop + plotH - frac * plotH;
                double value = frac * maxVal;
                var txt = new TextBlock
                {
                    Text = $"{value:F0}",
                    Foreground = _textBrush,
                    FontSize = 12
                };
                Canvas.SetLeft(txt, 4);
                Canvas.SetTop(txt, y - 8);
                _canvas.Children.Add(txt);

                // light grid
                var gridLine = new Line
                {
                    StartPoint = new Point(marginLeft, y),
                    EndPoint = new Point(marginLeft + plotW, y),
                    Stroke = SolidColorBrush.Parse("#F1F6F6"),
                    StrokeThickness = 1
                };
                _canvas.Children.Add(gridLine);
            }

            // plot data
            if (_useBars)
            {
                double slot = plotW / n;
                double barW = Math.Max(2, slot * 0.7);
                for (int i = 0; i < n; i++)
                {
                    double v = data[i];
                    double h = (v / maxVal) * plotH;
                    double x = marginLeft + i * slot + (slot - barW) / 2;
                    double y = marginTop + plotH - h;
                    var rect = new Rectangle
                    {
                        Width = barW,
                        Height = Math.Max(1, h),
                        Fill = _barBrush,
                        Stroke = null,
                        RadiusX = 2,
                        RadiusY = 2
                    };
                    Canvas.SetLeft(rect, x);
                    Canvas.SetTop(rect, y);
                    _canvas.Children.Add(rect);
                }
            }
            else
            {
                // draw lines segment-by-segment to avoid PointCollection dependency
                double slot = plotW / Math.Max(1, n - 1);
                Point? prev = null;
                var pointsList = new List<Point>();
                for (int i = 0; i < n; i++)
                {
                    double v = data[i];
                    double y = marginTop + plotH - (v / maxVal) * plotH;
                    double x = marginLeft + i * slot;
                    var p = new Point(x, y);
                    if (prev != null)
                    {
                        var seg = new Line
                        {
                            StartPoint = prev.Value,
                            EndPoint = p,
                            Stroke = _lineBrush,
                            StrokeThickness = 2
                        };
                        _canvas.Children.Add(seg);
                    }
                    pointsList.Add(p);
                    prev = p;
                }

                // draw small circles at points
                foreach (var p in pointsList)
                {
                    var dot = new Ellipse
                    {
                        Width = 6,
                        Height = 6,
                        Fill = _lineBrush,
                        Stroke = Brushes.White,
                        StrokeThickness = 1
                    };
                    Canvas.SetLeft(dot, p.X - 3);
                    Canvas.SetTop(dot, p.Y - 3);
                    _canvas.Children.Add(dot);
                }
            }

            // X labels (show a few)
            int step = Math.Max(1, n / 8);
            double slotLabel = plotW / n;
            for (int i = 0; i < n; i += step)
            {
                double x = marginLeft + i * slotLabel + slotLabel / 2;
                var lbl = new TextBlock
                {
                    Text = $"{i + 1}",
                    Foreground = _textBrush,
                    FontSize = 11
                };
                Canvas.SetLeft(lbl, x - 8);
                Canvas.SetTop(lbl, marginTop + plotH + 4);
                _canvas.Children.Add(lbl);
            }

            // legend
            var legend = new TextBlock
            {
                Text = _showVolume ? "Volumen (m³)" : "Caudal (m³/s)",
                Foreground = _textBrush,
                FontSize = 13,
                FontWeight = FontWeight.Bold
            };
            Canvas.SetLeft(legend, marginLeft + 6);
            Canvas.SetTop(legend, 0);
            _canvas.Children.Add(legend);
        }
    }
}