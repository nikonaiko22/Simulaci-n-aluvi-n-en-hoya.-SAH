using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using System;
using System.IO;
using System.Threading.Tasks;

namespace SAH.UI
{
    public partial class App : Application
    {
        private const int DefaultSplashMs = 5000;
        private const string LogFile = "sah_error.txt";

        public override void Initialize() => AvaloniaXamlLoader.Load(this);

        public override async void OnFrameworkInitializationCompleted()
        {
            try
            {
                try { File.AppendAllText(LogFile, $"App start: {DateTime.Now:O}{Environment.NewLine}"); } catch { }

                if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
                {
                    // Evitar que cerrar la splash cierre la app
                    desktop.ShutdownMode = ShutdownMode.OnMainWindowClose;

                    int splashMs = DefaultSplashMs;

                    // Leer variable de entorno de forma segura (env puede ser null)
                    string? env = null;
                    try
                    {
                        env = Environment.GetEnvironmentVariable("SPLASH_MS");
                    }
                    catch { /* ignorar errores al leer env */ }

                    if (!string.IsNullOrWhiteSpace(env) && int.TryParse(env, out var v) && v >= 0)
                    {
                        splashMs = v;
                    }

                    // Mostrar splash primero
                    SplashWindow? splash = null;
                    try
                    {
                        splash = new SplashWindow { Topmost = true };
                        splash.Show();
                        try { File.AppendAllText(LogFile, "Show splash OK\n"); } catch { }
                    }
                    catch (Exception ex)
                    {
                        try { File.AppendAllText(LogFile, $"Show splash failed: {ex}{Environment.NewLine}"); } catch { }
                        splash = null;
                    }

                    // Ejecutar animación/progreso del splash
                    try
                    {
                        if (splash != null && splashMs > 0)
                            await splash.RunForMillisecondsAsync(splashMs);
                        else
                            await Task.Delay(splashMs);
                        try { File.AppendAllText(LogFile, $"Splash waited {splashMs}ms\n"); } catch { }
                    }
                    catch (Exception ex)
                    {
                        try { File.AppendAllText(LogFile, $"Splash Run failed: {ex}{Environment.NewLine}"); } catch { }
                    }

                    // Cerrar splash
                    try
                    {
                        if (splash != null)
                        {
                            splash.Close();
                            await Task.Delay(50); // dar tiempo al loop UI
                            try { File.AppendAllText(LogFile, "Splash closed\n"); } catch { }
                        }
                    }
                    catch (Exception ex)
                    {
                        try { File.AppendAllText(LogFile, $"Close splash failed: {ex}{Environment.NewLine}"); } catch { }
                    }

                    // Crear y mostrar MainWindow SOLO DESPUÉS de cerrar splash
                    try
                    {
                        var main = new MainWindow();
                        desktop.MainWindow = main;
                        main.Show();
                        main.Activate();
                        try { File.AppendAllText(LogFile, "Main shown\n"); } catch { }
                    }
                    catch (Exception ex)
                    {
                        try { File.AppendAllText(LogFile, $"Show main failed: {ex}{Environment.NewLine}"); } catch { }
                        try { desktop.Shutdown(); } catch { Environment.Exit(1); }
                    }
                }
            }
            catch (Exception exOuter)
            {
                try { File.AppendAllText(LogFile, $"OnFrameworkInitializationCompleted outer exception: {exOuter}{Environment.NewLine}"); } catch { }
                try { Environment.Exit(1); } catch { }
            }

            base.OnFrameworkInitializationCompleted();
        }
    }
}