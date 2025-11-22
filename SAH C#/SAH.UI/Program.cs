using System;
using Avalonia;
using Avalonia.ReactiveUI;

namespace SAH.UI
{
    internal class Program
    {
        // Initialization code. Don't use any Avalonia types before AppMain is called: things aren't initialized yet.
        public static void Main(string[] args) => BuildAvaloniaApp()
            .StartWithClassicDesktopLifetime(args);

        // Avalonia configuration, don't remove; also used by visual designer.
        public static AppBuilder BuildAvaloniaApp()
            => AppBuilder.Configure<App>()
                         .UsePlatformDetect()
                         .LogToTrace()
                         .UseReactiveUI();
    }
}