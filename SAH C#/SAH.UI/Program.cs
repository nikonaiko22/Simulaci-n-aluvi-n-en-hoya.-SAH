using Avalonia;
using Avalonia.ReactiveUI;
using System;

namespace SAH.UI
{
    internal class Program
    {
        // Entry point. Leave as-is.
        public static void Main(string[] args) => BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);

        public static AppBuilder BuildAvaloniaApp()
            => AppBuilder.Configure<App>()
                         .UsePlatformDetect()
                         .LogToTrace()
                         .UseReactiveUI();
    }
}