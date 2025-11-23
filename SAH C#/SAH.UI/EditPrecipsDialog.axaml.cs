using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Input;
using System;
using System.Linq;
using System.Collections.Generic;
using SAH.UI.ViewModels;

namespace SAH.UI
{
    public partial class EditPrecipsDialog : Window
    {
        private StackPanel _gridPanel = null!; // initialized after InitializeComponent
        private List<(TextBox p, TextBox ce, TextBox cm)> _rows = new List<(TextBox, TextBox, TextBox)>();
        private MainWindowViewModel? _vm;

        public EditPrecipsDialog() { InitializeComponent(); }

        public EditPrecipsDialog(int count, MainWindowViewModel? vm = null)
        {
            InitializeComponent();
            _gridPanel = this.FindControl<StackPanel>("GridPanel")!;
            _vm = vm;

            // prefill from VM
            string[] lines = Array.Empty<string>();
            if (vm != null)
            {
                var txt = vm.GetPrecipsText();
                lines = txt.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                count = Math.Max(count, lines.Length);
            }

            for (int i = 0; i < count; i++) AddRow(i < lines.Length ? lines[i] : null);

            var add = this.FindControl<Button>("AddRowBtn");
            var accept = this.FindControl<Button>("AcceptBtn");
            var cancel = this.FindControl<Button>("CancelBtn");
            var clearAll = this.FindControl<Button>("ClearAllBtn");

            if (add != null)
                add.Click += (_, __) => AddRow();

            if (clearAll != null)
                clearAll.Click += (_, __) =>
                {
                    _vm?.ClearPrecips();
                    _gridPanel.Children.Clear();
                    _rows.Clear();
                    Close(null);
                };

            if (accept != null)
                accept.Click += (_, __) =>
                {
                    var linesOut = _rows.Select(r =>
                    {
                        var pv = (r.p.Text ?? "0").Trim();
                        var cev = (r.ce.Text ?? "0.5").Trim();
                        var cmv = (r.cm.Text ?? "1.0").Trim();
                        return $"{pv},{cev},{cmv}";
                    }).Where(s => s.Length > 0).ToArray();
                    var outStr = string.Join("\r\n", linesOut);
                    if (_vm != null) _vm.ReplacePrecipsFromText(outStr);
                    Close(outStr);
                };

            if (cancel != null)
                cancel.Click += (_, __) => Close(null);
        }

        private void AddRow(string? prefill = null)
        {
            var sp = new StackPanel { Orientation = Avalonia.Layout.Orientation.Horizontal, Spacing = 8 };
            var lbl = new TextBlock { Text = $"{_rows.Count + 1}", Width = 28, VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center };
            var p = new TextBox { Width = 120, Watermark = "P_mm" };
            var ce = new TextBox { Width = 80, Watermark = "Ce" };
            var cm = new TextBox { Width = 80, Watermark = "Cm" };
            if (!string.IsNullOrEmpty(prefill))
            {
                var parts = prefill.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length > 0) p.Text = parts[0].Trim();
                if (parts.Length > 1) ce.Text = parts[1].Trim();
                if (parts.Length > 2) cm.Text = parts[2].Trim();
            }

            // Enter navigation: p -> ce -> cm -> next row p (creates row if needed)
            p.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter)
                {
                    ce.Focus();
                    e.Handled = true;
                }
            };
            ce.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter)
                {
                    cm.Focus();
                    e.Handled = true;
                }
            };

            sp.Children.Add(lbl);
            sp.Children.Add(p);
            sp.Children.Add(ce);
            sp.Children.Add(cm);
            _gridPanel.Children.Add(sp);
            _rows.Add((p, ce, cm));

            int thisIndex = _rows.Count - 1;
            cm.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter)
                {
                    int nextIdx = thisIndex + 1;
                    if (nextIdx < _rows.Count)
                    {
                        _rows[nextIdx].p.Focus();
                    }
                    else
                    {
                        AddRow();
                        _rows.Last().p.Focus();
                    }
                    e.Handled = true;
                }
            };
        }

        private void InitializeComponent() => AvaloniaXamlLoader.Load(this);
    }
}