using ReactiveUI;
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using SAH.UI.Models;
using SAH.Core;

namespace SAH.UI.ViewModels
{
    public class MainWindowViewModel : ReactiveObject
    {
        private double[] _areasKm2 = new double[] { 1.0, 0.5, 0.2 };
        private double[] _precips_mm = new double[] { 10.0, 5.0, 0.0, 2.0 };
        private double[] _ce = new double[] { 0.5, 0.6, 0.0, 0.4 };
        private double[] _cm = new double[] { 1.0, 1.0, 1.0, 1.0 };

        public ObservableCollection<ResultRow> Rows { get; } = new ObservableCollection<ResultRow>();

        private string _summaryText = string.Empty;
        public string SummaryText { get => _summaryText; set => this.RaiseAndSetIfChanged(ref _summaryText, value); }

        private bool _isBusy;
        public bool IsBusy { get => _isBusy; set => this.RaiseAndSetIfChanged(ref _isBusy, value); }

        private CancellationTokenSource _cts = new CancellationTokenSource();

        private string _qmaxDisplay = "-";
        public string QmaxDisplay { get => _qmaxDisplay; set => this.RaiseAndSetIfChanged(ref _qmaxDisplay, value); }

        private string _vmaxDisplay = "-";
        public string VmaxDisplay { get => _vmaxDisplay; set => this.RaiseAndSetIfChanged(ref _vmaxDisplay, value); }

        private string _totalVolumeDisplay = "-";
        public string TotalVolumeDisplay { get => _totalVolumeDisplay; set => this.RaiseAndSetIfChanged(ref _totalVolumeDisplay, value); }

        private string _timeToPeakDisplay = "-";
        public string TimeToPeakDisplay { get => _timeToPeakDisplay; set => this.RaiseAndSetIfChanged(ref _timeToPeakDisplay, value); }

        public MainWindowViewModel()
        {
            // No OxyPlot/PlotModel here — gráficos manejados por ChartControl
        }

        public int AreasCount => _areasKm2?.Length ?? 0;
        public int PrecipsCount => _precips_mm?.Length ?? 0;

        public (bool ok, string error) ParseAndSetAreasFromText(string text)
        {
            try
            {
                var arr = ParseNumbersFromText(text);
                if (arr.Length <= 0) return (false, "Se requieren al menos 1 área.");
                _areasKm2 = arr;
                SummaryText = $"Áreas guardadas (km²): {string.Join(", ", _areasKm2)}";
                this.RaisePropertyChanged(nameof(AreasCount));
                return (true, "");
            }
            catch (Exception ex) { return (false, ex.Message); }
        }

        public (bool ok, string error) ParseAndSetPrecipsFromText(string text)
        {
            try
            {
                var lines = text.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
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
                if (newP.Count == 0) return (false, "Se requieren al menos 1 fila.");
                _precips_mm = newP.ToArray();
                _ce = newCe.ToArray();
                _cm = newCm.ToArray();
                SummaryText = $"Precipitaciones guardadas (p={_precips_mm.Length}): P(mm)={string.Join(", ", _precips_mm)}";
                this.RaisePropertyChanged(nameof(PrecipsCount));
                return (true, "");
            }
            catch (Exception ex) { return (false, ex.Message); }
        }

        public async Task SimulateAsync(int a, int p)
        {
            _cts?.Cancel();
            _cts = new CancellationTokenSource();
            var token = _cts.Token;

            IsBusy = true;
            try
            {
                await Task.Delay(120, token);

                // Ajuste seguro de tamaños
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

                // convertir áreas a m2
                double[] A_m2 = new double[_areasKm2.Length];
                for (int i = 0; i < _areasKm2.Length; i++) A_m2[i] = _areasKm2[i] * 1e6;

                // Usar SAH.Core (debe existir)
                var Y = HydrologyCalculator.ComputeYFromHourVectors(_ce, _cm, a);
                var Q = HydrologyCalculator.ComputeQ(_precips_mm, Y, unitsMm: true);
                var V = HydrologyCalculator.ComputeV(A_m2, Q);
                var W = HydrologyCalculator.ComputeWFromV(V); // volumen por hora (m3)
                var flows = new double[W.Length];
                for (int i = 0; i < W.Length; i++) flows[i] = W[i] / 3600.0; // m3/s

                // rellenar filas
                Rows.Clear();
                for (int i = 0; i < W.Length; i++)
                {
                    Rows.Add(new ResultRow
                    {
                        Hour = i + 1,
                        Volume = $"{W[i]:F2}",
                        Flow = $"{flows[i]:F4}"
                    });
                }

                double qmax = flows.Max();
                int idxPeak = Array.IndexOf(flows, qmax);
                double vmax = W.Max();
                double totalVol = W.Sum();

                QmaxDisplay = $"{qmax:F2} m³/s";
                VmaxDisplay = $"{vmax:F2} m³";
                TotalVolumeDisplay = $"{totalVol:N0} m³";
                TimeToPeakDisplay = $"{(idxPeak + 1)} h";

                SummaryText = $"Simulación completada: Q[v]={QmaxDisplay}, V[v]={VmaxDisplay}.";

                await Task.Delay(180, token);
            }
            catch (OperationCanceledException) { }
            catch (Exception ex)
            {
                SummaryText = $"Error en cálculo: {ex.Message}";
            }
            finally
            {
                IsBusy = false;
            }
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
    }
}