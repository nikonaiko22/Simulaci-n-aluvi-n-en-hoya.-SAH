using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using System;
using System.Linq;
using SAH.UI.ViewModels;
using SAH.UI.Models;
using System.Threading.Tasks;
using SAH.UI.Controls;
using Avalonia.Controls.Primitives; // for ToggleButton.IsCheckedProperty
using System.Reactive.Linq;

namespace SAH.UI
{
    public partial class MainWindow : Window
    {
        private MainWindowViewModel _vm;

        public MainWindow()
        {
            InitializeComponent();
            _vm = new MainWindowViewModel();
            DataContext = _vm;

            // controls
            var editAreasBtn = this.FindControl<Button>("EditAreasBtn");
            var editPrecipsBtn = this.FindControl<Button>("EditPrecipsBtn");
            var simulateBtn = this.FindControl<Button>("SimulateBtn");
            var clearBtn = this.FindControl<Button>("ClearBtn");

            var aBox = this.FindControl<TextBox>("ABox");
            var pBox = this.FindControl<TextBox>("PBox");

            var qmaxText = this.FindControl<TextBlock>("QmaxText");
            var vmaxText = this.FindControl<TextBlock>("VmaxText");
            var totalVolText = this.FindControl<TextBlock>("TotalVolText");
            var resultsList = this.FindControl<ItemsControl>("ResultsList");
            var summaryBox = this.FindControl<TextBlock>("SummaryBox");
            var busyBar = this.FindControl<ProgressBar>("BusyBar");

            var chartLineRb = this.FindControl<RadioButton>("GraphTypeLine");
            var chartBarsRb = this.FindControl<RadioButton>("GraphTypeBars");
            var chartMetric = this.FindControl<ComboBox>("ChartMetric");
            var mainChart = this.FindControl<ChartControl>("MainChart");

            // initial UI state
            if (aBox != null) aBox.Text = _vm.AreasCount.ToString();
            if (pBox != null) pBox.Text = _vm.PrecipsCount.ToString();
            if (resultsList != null) resultsList.ItemsSource = _vm.Rows;
            if (summaryBox != null) summaryBox.Text = _vm.SummaryText;

            // chart option changes
            void UpdateChartMode()
            {
                if (mainChart == null) return;
                bool useBars = chartBarsRb?.IsChecked ?? false;
                bool showVolume = (chartMetric?.SelectedIndex ?? 0) == 0;
                mainChart.SetMode(useBars, showVolume);
            }

            // Use observables on IsChecked to avoid obsolete Checked event
            if (chartLineRb != null)
                chartLineRb.GetObservable(ToggleButton.IsCheckedProperty)
                           .Subscribe(_ => UpdateChartMode());
            if (chartBarsRb != null)
                chartBarsRb.GetObservable(ToggleButton.IsCheckedProperty)
                           .Subscribe(_ => UpdateChartMode());
            if (chartMetric != null)
                chartMetric.SelectionChanged += (_, __) => UpdateChartMode();

            if (editAreasBtn != null)
            {
                editAreasBtn.Click += async (_, __) =>
                {
                    int a = int.TryParse(aBox?.Text, out var aa) ? aa : _vm.AreasCount;
                    var dlg = new EditAreasDialog(a, _vm);
                    var result = await dlg.ShowDialog<string?>(this);
                    if (result != null)
                    {
                        var (ok, err) = _vm.ParseAndSetAreasFromText(result);
                        if (!ok) await MessageBox("Error", err);
                        else if (aBox != null) aBox.Text = _vm.AreasCount.ToString();
                    }
                };
            }

            if (editPrecipsBtn != null)
            {
                editPrecipsBtn.Click += async (_, __) =>
                {
                    int p = int.TryParse(pBox?.Text, out var pp) ? pp : _vm.PrecipsCount;
                    var dlg = new EditPrecipsDialog(p, _vm);
                    var result = await dlg.ShowDialog<string?>(this);
                    if (result != null)
                    {
                        var (ok, err) = _vm.ParseAndSetPrecipsFromText(result);
                        if (!ok) await MessageBox("Error", err);
                        else if (pBox != null) pBox.Text = _vm.PrecipsCount.ToString();
                    }
                };
            }

            if (simulateBtn != null)
            {
                simulateBtn.Click += async (_, __) =>
                {
                    if (!int.TryParse(aBox?.Text ?? "0", out var a) || !int.TryParse(pBox?.Text ?? "0", out var p))
                    {
                        await MessageBox("Error", "a y p deben ser enteros positivos");
                        return;
                    }
                    if (a <= 0 || p <= 0) { await MessageBox("Error", "a y p deben ser mayores que cero"); return; }

                    if (busyBar != null) busyBar.IsVisible = true;
                    try
                    {
                        await _vm.SimulateAsync(a, p);

                        // update small UI pieces
                        if (qmaxText != null) qmaxText.Text = _vm.QmaxDisplay;
                        if (vmaxText != null) vmaxText.Text = _vm.VmaxDisplay;
                        if (totalVolText != null) totalVolText.Text = _vm.TotalVolumeDisplay;
                        if (resultsList != null) resultsList.ItemsSource = _vm.Rows;
                        if (summaryBox != null) summaryBox.Text = _vm.SummaryText;

                        // provide data to chart control: volumes (W array) and flows
                        var volumes = _vm.Rows.Select(r => double.TryParse(r.Volume, out var v) ? v : 0.0).ToArray();
                        var flows = _vm.Rows.Select(r => double.TryParse(r.Flow, out var f) ? f : 0.0).ToArray();

                        mainChart?.SetData(volumes, flows);
                        UpdateChartMode();
                    }
                    finally
                    {
                        if (busyBar != null) busyBar.IsVisible = false;
                    }
                };
            }

            if (clearBtn != null)
            {
                clearBtn.Click += (_, __) =>
                {
                    _vm.Rows.Clear();
                    _vm.SummaryText = "";
                    if (resultsList != null) resultsList.ItemsSource = _vm.Rows;
                    if (summaryBox != null) summaryBox.Text = _vm.SummaryText;
                    if (qmaxText != null) qmaxText.Text = "-";
                    if (vmaxText != null) vmaxText.Text = "-";
                    if (totalVolText != null) totalVolText.Text = "-";
                    mainChart?.SetData(Array.Empty<double>(), Array.Empty<double>());
                };
            }

            _vm.PropertyChanged += (_, __) =>
            {
                if (summaryBox != null) summaryBox.Text = _vm.SummaryText;
            };
        }

        private void InitializeComponent() => AvaloniaXamlLoader.Load(this);

        private async Task MessageBox(string title, string message)
        {
            var tb = new TextBox { Text = message, IsReadOnly = true, AcceptsReturn = true, Height = 220 };
            var ok = new Button { Content = "Cerrar", Width = 90, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Right };
            var panel = new StackPanel { Margin = new Thickness(8) };
            panel.Children.Add(tb);
            panel.Children.Add(ok);
            var dlg = new Window { Title = title, Width = 600, Height = 360, Content = panel };
            ok.Click += (_, __) => dlg.Close();
            await dlg.ShowDialog(this);
        }
    }
}