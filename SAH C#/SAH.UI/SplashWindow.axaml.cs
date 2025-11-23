using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Threading;
using System;
using System.Threading.Tasks;

namespace SAH.UI
{
    public partial class SplashWindow : Window
    {
        public SplashWindow()
        {
            InitializeComponent();
        }

        private void InitializeComponent() => AvaloniaXamlLoader.Load(this);

        // Ejecuta el progreso durante 'ms' milisegundos y actualiza la barra/status.
        public async Task RunForMillisecondsAsync(int ms)
        {
            if (ms <= 0) return;

            var progressBar = this.FindControl<ProgressBar>("Pb");
            var status = this.FindControl<TextBlock>("StatusText");

            // Si no encuentra controles, salir (y dejar que el caller lo registre)
            if (progressBar == null || status == null)
                return;

            // Asegurar que no está en indeterminate
            Dispatcher.UIThread.Post(() => progressBar.IsIndeterminate = false, DispatcherPriority.Render);

            const int steps = 100;
            int delay = Math.Max(1, ms / steps);

            for (int i = 0; i <= steps; i++)
            {
                int value = i; // 0..100

                // Actualizar UI con prioridad Render para asegurar repintado
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    progressBar.Value = value;
                    if (value < 30) status.Text = "Cargando recursos...";
                    else if (value < 70) status.Text = "Inicializando UI...";
                    else if (value < 100) status.Text = "Finalizando...";
                    else status.Text = "Listo";
                }, DispatcherPriority.Render);

                // Ceder para que el UI se actualice (no bloquear hilo UI)
                await Task.Delay(delay);
            }
        }

        // Método para actualizar texto desde fuera
        public void SetStatus(string text)
        {
            Dispatcher.UIThread.Post(() =>
            {
                var tb = this.FindControl<TextBlock>("StatusText");
                if (tb != null) tb.Text = text;
            }, DispatcherPriority.Render);
        }
    }
}