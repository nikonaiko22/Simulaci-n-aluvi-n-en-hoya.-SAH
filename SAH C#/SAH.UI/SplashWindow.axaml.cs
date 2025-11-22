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

        private void InitializeComponent()
        {
            AvaloniaXamlLoader.Load(this);
        }

        // Ejecuta el progreso durante ms milisegundos y actualiza la barra/status.
        public async Task RunForMillisecondsAsync(int ms)
        {
            if (ms <= 0) return;

            var progressBar = this.FindControl<ProgressBar>("Pb");
            var status = this.FindControl<TextBlock>("StatusText");

            const int steps = 100;
            int delay = Math.Max(1, ms / steps);

            for (int i = 0; i <= steps; i++)
            {
                int value = i; // 0..100
                // Actualizar UI en el hilo correcto
                Dispatcher.UIThread.Post(() =>
                {
                    if (progressBar != null) progressBar.Value = value;
                    if (status != null)
                    {
                        if (value < 30) status.Text = "Cargando recursos...";
                        else if (value < 70) status.Text = "Inicializando UI...";
                        else if (value < 100) status.Text = "Finalizando...";
                        else status.Text = "Listo";
                    }
                }, DispatcherPriority.Background);

                await Task.Delay(delay);
            }
        }

        // Método para actualizar el texto desde fuera si lo deseas
        public void SetStatus(string text)
        {
            var tb = this.FindControl<TextBlock>("StatusText");
            if (tb != null)
                Dispatcher.UIThread.Post(() => tb.Text = text);
        }
    }
}