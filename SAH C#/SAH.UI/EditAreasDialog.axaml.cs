using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using System;
using System.Linq;
using System.Collections.Generic;

namespace SAH.UI
{
    public partial class EditAreasDialog : Window
    {
        private StackPanel _inputsPanel = null!; // initialized after InitializeComponent
        private List<TextBox> _boxes = new List<TextBox>();

        public EditAreasDialog()
        {
            InitializeComponent();
            _inputsPanel = this.FindControl<StackPanel>("InputsPanel")!;
        }

        public EditAreasDialog(int count, object? vm = null) : this()
        {
            // create rows
            for (int i = 0; i < count; i++)
            {
                var sp = new StackPanel { Orientation = Avalonia.Layout.Orientation.Horizontal, Spacing = 8 };
                var lbl = new TextBlock { Text = $"{i + 1}", Width = 28, VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center };
                var tb = new TextBox { Width = 240, Watermark = "km²" };
                sp.Children.Add(lbl);
                sp.Children.Add(tb);
                _inputsPanel.Children.Add(sp);
                _boxes.Add(tb);
            }

            var accept = this.FindControl<Button>("AcceptBtn");
            var cancel = this.FindControl<Button>("CancelBtn");

            if (accept != null)
                accept.Click += (_, __) =>
                {
                    // gather values as newline separated list
                    var vals = _boxes.Select(b => (b.Text ?? "0").Trim())
                                     .Where(s => s.Length > 0)
                                     .ToArray();
                    var outStr = string.Join("\r\n", vals);
                    Close(outStr);
                };

            if (cancel != null)
                cancel.Click += (_, __) => Close(null);
        }

        private void InitializeComponent()
        {
            AvaloniaXamlLoader.Load(this);
        }
    }
}