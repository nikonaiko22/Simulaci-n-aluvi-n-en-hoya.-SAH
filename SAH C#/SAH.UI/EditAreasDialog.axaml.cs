using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using System;
using System.Linq;
using System.Collections.Generic;
using SAH.UI.ViewModels;

namespace SAH.UI
{
    public partial class EditAreasDialog : Window
    {
        private StackPanel _inputsPanel = null!; // initialized after InitializeComponent
        private List<TextBox> _boxes = new List<TextBox>();
        private MainWindowViewModel? _vm;

        public EditAreasDialog()
        {
            InitializeComponent();
            _inputsPanel = this.FindControl<StackPanel>("InputsPanel")!;
        }

        // Accept vm to prefill and allow direct operations (memory)
        public EditAreasDialog(int count, MainWindowViewModel? vm = null) : this()
        {
            _vm = vm;
            // prefill values from VM if available
            string[] values;
            if (vm != null)
            {
                var txt = vm.GetAreasText();
                values = txt.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                // ensure count at least matches values length
                count = Math.Max(count, values.Length);
            }
            else
            {
                values = new string[0];
            }

            // create rows
            for (int i = 0; i < count; i++)
            {
                var sp = new StackPanel { Orientation = Avalonia.Layout.Orientation.Horizontal, Spacing = 8 };
                var lbl = new TextBlock { Text = $"{i + 1}", Width = 28, VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center };
                var tb = new TextBox { Width = 240, Watermark = "km²", Text = i < values.Length ? values[i] : "" };
                sp.Children.Add(lbl);
                sp.Children.Add(tb);
                _inputsPanel.Children.Add(sp);
                _boxes.Add(tb);
            }

            var accept = this.FindControl<Button>("AcceptBtn");
            var cancel = this.FindControl<Button>("CancelBtn");
            var clearAll = this.FindControl<Button>("ClearAllBtn");
            var normalize = this.FindControl<Button>("NormalizeBtn");

            if (normalize != null)
                normalize.Click += (_, __) =>
                {
                    // optional: normalize so they sum to 1 (example)
                    var nums = _boxes.Select(b => double.TryParse(b.Text, out var v) ? v : 0.0).ToArray();
                    var s = nums.Sum();
                    if (s == 0) return;
                    for (int i = 0; i < nums.Length; i++) _boxes[i].Text = (nums[i] / s).ToString("G");
                };

            if (clearAll != null)
                clearAll.Click += (_, __) =>
                {
                    // clear VM data and UI
                    _vm?.ClearAreas();
                    foreach (var b in _boxes) b.Text = "";
                    Close(null);
                };

            if (accept != null)
                accept.Click += (_, __) =>
                {
                    // gather values as newline separated list
                    var vals = _boxes.Select(b => (b.Text ?? "0").Trim())
                                     .Where(s => s.Length > 0)
                                     .ToArray();
                    var outStr = string.Join("\r\n", vals);
                    // Optionally update VM directly for memory
                    if (_vm != null)
                    {
                        _vm.ReplaceAreasFromText(outStr);
                    }
                    Close(outStr);
                };

            if (cancel != null)
                cancel.Click += (_, __) => Close(null);
        }

        private void InitializeComponent()
        {
            AvaloniaXamlLoader.Load(this);
            _inputsPanel = this.FindControl<StackPanel>("InputsPanel")!;
        }
    }
}