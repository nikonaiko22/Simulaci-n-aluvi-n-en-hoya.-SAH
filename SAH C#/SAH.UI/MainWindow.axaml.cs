using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Layout;
using Avalonia.Media;
using System;
using System.Collections.ObjectModel;
using SAH.Core;
using SAH.UI.Models;

namespace SAH.UI
{
    public partial class MainWindow : Window
    {
        private ObservableCollection<ResultRow> _rows = new ObservableCollection<ResultRow>();

        // default data
        private double[] _areasKm2 = new double[] { 1.0, 0.5, 0.2 };
        private double[] _precips_mm = new double[] { 10.0, 5.0, 0.0, 2.0 };
        private double[] _ce = new double[] { 0.5, 0.6, 0.0, 0.4 };
        private double[] _cm = new double[] { 1.0, 1.0, 1.0, 1.0 };

        public MainWindow()
        {
            AvaloniaXamlLoader.Load(this);

            var aBox = this.FindControl<TextBox>("ABox");
            var pBox = this.FindControl<TextBox>("PBox");
            var editAreasBtn = this.FindControl<Button>("EditAreasBtn");
            var editPrecipsBtn = this.FindControl<Button>("EditPrecipsBtn");
            var simulateBtn = this.FindControl<Button>("SimulateBtn");
            var showResultsBtn = this.FindControl<Button>("ShowResultsBtn");
            var resultsList = this.FindControl<ItemsControl>("ResultsList");

            if (aBox != null) aBox.Text = _areasKm2.Length.ToString();
            if (pBox != null) pBox.Text = _precips_mm.Length.ToString();

            if (editAreasBtn != null) editAreasBtn.Click += EditAreasBtn_Click;
            if (editPrecipsBtn != null) editPrecipsBtn.Click += EditPrecipsBtn_Click;
            if (simulateBtn != null) simulateBtn.Click += SimulateBtn_Click;
            if (showResultsBtn != null) showResultsBtn.Click += ShowResultsBtn_Click;

            if (resultsList != null) resultsList.ItemsSource = _rows;

            AppendSummary("Interfaz lista. Pulsa 'Simular' para calcular con valores por defecto.");
        }

        private void AppendSummary(string s)
        {
            var sb = this.FindControl<TextBox>("SummaryBox");
            if (sb != null) sb.Text = sb.Text + s + Environment.NewLine;
        }

        private async void EditAreasBtn_Click(object? sender, RoutedEventArgs e)
        {
            string prefill = string.Join("\n", _areasKm2);
            var editor = new MultiLineEditorWindow("Editar Áreas (km²) - una por línea o separadas por coma", prefill);
            var result = await editor.ShowDialog<string?>(this);
            if (result != null)
            {
                try
                {
                    var arr = ParseNumbersFromText(result);
                    if (arr.Length <= 0) throw new Exception("Se requieren al menos 1 área.");
                    _areasKm2 = arr;
                    var aBox = this.FindControl<TextBox>("ABox");
                    if (aBox != null) aBox.Text = _areasKm2.Length.ToString();
                    AppendSummary($"Áreas guardadas (km²): {string.Join(", ", _areasKm2)}");
                }
                catch (Exception ex)
                {
                    await MessageBox("Error", $"Valores inválidos: {ex.Message}");
                }
            }
        }

        private async void EditPrecipsBtn_Click(object? sender, RoutedEventArgs e)
        {
            int p = _precips_mm.Length;
            System.Text.StringBuilder sb = new System.Text.StringBuilder();
            for (int i = 0; i < p; i++)
                sb.AppendLine($"{_precips_mm[i]},{_ce[i]},{_cm[i]}");
            var editor = new MultiLineEditorWindow("Editar Precipitaciones (P_mm,Ce,Cm) - una por línea", sb.ToString());
            var result = await editor.ShowDialog<string?>(this);
            if (result != null)
            {
                try
                {
                    var lines = result.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                    var newP = new System.Collections.Generic.List<double>();
                    var newCe = new System.Collections.Generic.List<double>();
                    var newCm = new System.Collections.Generic.List<double>();
                    foreach (var line in lines)
                    {
                        var parts = line.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length < 1) continue;
                        double pval = double.Parse(parts[0].Trim());
                        double ceVal = parts.Length > 1 ? double.Parse(parts[1].Trim()) : 0.5;
                        double cmVal = parts.Length > 2 ? double.Parse(parts[2].Trim()) : 1.0;
                        newP.Add(pval); newCe.Add(ceVal); newCm.Add(cmVal);
                    }
                    if (newP.Count == 0) throw new Exception("Se requieren al menos 1 fila.");
                    _precips_mm = newP.ToArray();
                    _ce = newCe.ToArray();
                    _cm = newCm.ToArray();
                    var pBox = this.FindControl<TextBox>("PBox");
                    if (pBox != null) pBox.Text = _precips_mm.Length.ToString();
                    AppendSummary($"Precipitaciones guardadas (p={_precips_mm.Length}): P(mm)={string.Join(", ", _precips_mm)}");
                }
                catch (Exception ex)
                {
                    await MessageBox("Error", $"Valores inválidos: {ex.Message}");
                }
            }
        }

        private async void SimulateBtn_Click(object? sender, RoutedEventArgs e)
        {
            int a, p;
            var aBox = this.FindControl<TextBox>("ABox");
            var pBox = this.FindControl<TextBox>("PBox");
            try
            {
                a = int.Parse(aBox?.Text ?? "0");
                p = int.Parse(pBox?.Text ?? "0");
            }
            catch
            {
                await MessageBox("Error", "a y p deben ser enteros.");
                return;
            }
            if (a <= 0 || p <= 0)
            {
                await MessageBox("Error", "a y p deben ser positivos.");
                return;
            }

            if (_areasKm2.Length != a)
            {
                var tmp = new double[a];
                for (int i = 0; i < a; i++) tmp[i] = i < _areasKm2.Length ? _areasKm2[i] : 0.0;
                _areasKm2 = tmp;
            }
            if (_precips_mm.Length < p)
            {
                var listP = new System.Collections.Generic.List<double>(_precips_mm);
                var listCe = new System.Collections.Generic.List<double>(_ce);
                var listCm = new System.Collections.Generic.List<double>(_cm);
                while (listP.Count < p) { listP.Add(0.0); listCe.Add(0.5); listCm.Add(1.0); }
                _precips_mm = listP.ToArray(); _ce = listCe.ToArray(); _cm = listCm.ToArray();
            }
            if (_precips_mm.Length > p)
            {
                Array.Resize(ref _precips_mm, p); Array.Resize(ref _ce, p); Array.Resize(ref _cm, p);
            }

            try
            {
                double[] A_m2 = new double[_areasKm2.Length];
                for (int i = 0; i < _areasKm2.Length; i++) A_m2[i] = _areasKm2[i] * 1e6;

                var Y = HydrologyCalculator.ComputeYFromHourVectors(_ce, _cm, a);
                var Q = HydrologyCalculator.ComputeQ(_precips_mm, Y, unitsMm: true);
                var V = HydrologyCalculator.ComputeV(A_m2, Q);
                var W = HydrologyCalculator.ComputeWFromV(V);
                var flows = new double[W.Length];
                for (int i = 0; i < W.Length; i++) flows[i] = W[i] / 3600.0;

                _rows.Clear();
                for (int i = 0; i < W.Length; i++)
                {
                    _rows.Add(new ResultRow
                    {
                        Hour = i + 1,
                        Volume = $"{W[i]:F2}",
                        Flow = $"{flows[i]:F4}"
                    });
                }

                var maxIdx = 0; for (int i = 0; i < flows.Length; i++) if (flows[i] > flows[maxIdx]) maxIdx = i;
                var maxVolIdx = 0; for (int i = 0; i < W.Length; i++) if (W[i] > W[maxVolIdx]) maxVolIdx = i;

                var summary = $"---- RESULTADOS ----{Environment.NewLine}";
                summary += $"Áreas (km²): {string.Join(", ", _areasKm2)}{Environment.NewLine}";
                summary += $"Precipitaciones P (mm): {string.Join(", ", _precips_mm)}{Environment.NewLine}";
                summary += $"Coef Escorr. Ce: {string.Join(", ", _ce)}{Environment.NewLine}";
                summary += $"Coef Mezcla Cm: {string.Join(", ", _cm)}{Environment.NewLine}";
                summary += $"Duración (h) = a + p - 1 = {a + p - 1}{Environment.NewLine}{Environment.NewLine}";
                summary += $"Hora crítica (máx caudal): {maxIdx + 1} -> {flows[maxIdx]:F4} m³/s{Environment.NewLine}";
                summary += $"Volumen máximo por hora: {W[maxVolIdx]:F2} m³ en hora {maxVolIdx + 1}{Environment.NewLine}";

                var summaryBox = this.FindControl<TextBox>("SummaryBox");
                if (summaryBox != null) summaryBox.Text = summary;
            }
            catch (Exception ex)
            {
                await MessageBox("Error en cálculo", ex.Message);
            }
        }

        private async void ShowResultsBtn_Click(object? sender, RoutedEventArgs e)
        {
            var summaryBox = this.FindControl<TextBox>("SummaryBox");
            await MessageBox("Resumen", summaryBox?.Text ?? "");
        }

        private double[] ParseNumbersFromText(string text)
        {
            var list = new System.Collections.Generic.List<double>();
            var lines = text.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (var line in lines)
            {
                var parts = line.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
                foreach (var p in parts)
                {
                    var tok = p.Trim();
                    if (tok.Length == 0) continue;
                    list.Add(double.Parse(tok));
                }
            }
            return list.ToArray();
        }

        private async System.Threading.Tasks.Task MessageBox(string title, string message)
        {
            var tb = new TextBox { Text = message, IsReadOnly = true, AcceptsReturn = true, Height = 200 };
            var scroll = new ScrollViewer { Content = tb, Height = 200 };

            var closeButton = new Button
            {
                Content = "Cerrar",
                HorizontalAlignment = HorizontalAlignment.Right,
                Width = 90,
            };
            closeButton.Click += (_, __) => { /* will be wired below via local dlg */ };

            var buttonsPanel = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                HorizontalAlignment = HorizontalAlignment.Right,
                Spacing = 8,
                Children = { closeButton }
            };

            var dlg = new Window
            {
                Title = title,
                Width = 500,
                Height = 300,
                Content = new StackPanel
                {
                    Margin = new Thickness(8),
                    Children =
                    {
                        scroll,
                        buttonsPanel
                    }
                }
            };

            // wire close
            closeButton.Click += (_,__) => dlg.Close();

            await dlg.ShowDialog(this);
        }

        private class MultiLineEditorWindow : Window
        {
            private TextBox _editor;
            private string _title;
            public MultiLineEditorWindow(string title, string initial)
            {
                _title = title;
                Title = title;
                Width = 600;
                Height = 400;
                _editor = new TextBox { AcceptsReturn = true, Text = initial ?? "" };
                var scroll = new ScrollViewer { Content = _editor, Height = 260 };

                var ok = new Button { Content = "OK", Width = 90 };
                var cancel = new Button { Content = "Cancelar", Width = 90 };
                ok.Click += (_,__) => Close(_editor.Text);
                cancel.Click += (_,__) => Close(null);
                var buttons = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    HorizontalAlignment = HorizontalAlignment.Right,
                    Spacing = 8,
                    Children = { ok, cancel }
                };
                Content = new StackPanel { Margin = new Thickness(8), Spacing = 6, Children = { scroll, buttons } };
            }
        }
    }
}