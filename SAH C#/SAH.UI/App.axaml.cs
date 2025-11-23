using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using Avalonia.Threading;
using System.Threading.Tasks;

namespace SAH.UI
{
    public partial class App : Application
    {
        public override void Initialize()
        {
            AvaloniaXamlLoader.Load(this);
        }

        public override void OnFrameworkInitializationCompleted()
        {
            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                // Create splash and start initialization asynchronously.
                var splash = new SplashWindow();
                splash.Show();

                // Fire-and-forget async startup that uses await but does not block UI thread.
                _ = StartWithSplashAsync(splash, desktop);
            }

            base.OnFrameworkInitializationCompleted();
        }

        private async Task StartWithSplashAsync(SplashWindow splash, IClassicDesktopStyleApplicationLifetime desktop)
        {
            try
            {
                // Run splash animation/progress. This method itself uses Dispatcher to update UI.
                await splash.RunForMillisecondsAsync(1200);

                // Optional: do additional initialization here (load resources, DB, etc.)
                // await SomeInitializationAsync();

                // Create main window on UI thread and show it.
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    var main = new MainWindow();
                    desktop.MainWindow = main;
                    main.Show();

                    // Close the splash window
                    splash.Close();
                });
            }
            catch
            {
                // If something fails during startup, ensure we still try to show main or close splash.
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    try
                    {
                        var main = new MainWindow();
                        desktop.MainWindow = main;
                        main.Show();
                    }
                    catch { }
                    try { splash.Close(); } catch { }
                });
                throw;
            }
        }
    }
}