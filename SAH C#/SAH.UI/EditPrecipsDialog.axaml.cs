using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using System;
using System.Linq;
using System.Collections.Generic;

namespace SAH.UI
{
    public partial class EditPrecipsDialog : Window
    {
        private StackPanel _gridPanel = null!; // initialized after InitializeComponent
        private List<(TextBox p, TextBox ce, TextBox cm)> _rows = new List<(TextBox, TextBox, TextBox)>();

        public EditPrecipsDialog() { InitializeComponent(); }

        public EditPrecipsDialog(int count, object? vm = null)
        {
            InitializeComponent();
            _gridPanel = this.FindControl<StackPanel>("GridPanel")!;

            for (int i = 0; i < count; i++) AddRow();

            var add = this.FindControl<Button>("AddRowBtn");
            var accept = this.FindControl<Button>("AcceptBtn");
            var cancel = this.FindControl<Button>("CancelBtn");

            if (add != null)
                add.Click += (_, __) => AddRow();

            if (accept != null)
                accept.Click += (_, __) =>
                {
                    var lines = _rows.Select(r =>
                    {
                        var pv = (r.p.Text ?? "0").Trim();
                        var cev = (r.ce.Text ?? "0.5").Trim();
                        var cmv = (r.cm.Text ?? "1.0").Trim();
                        return $"{pv},{cev},{cmv}";
                    }).ToArray();
                    Close(string.Join("\r\n", lines));
                };

            if (cancel != null)
                cancel.Click += (_, __) => Close(null);
        }

        private void AddRow()
        {
            var sp = new StackPanel { Orientation = Avalonia.Layout.Orientation.Horizontal, Spacing = 8 };
            var lbl = new TextBlock { Text = $"{_rows.Count + 1}", Width = 28, VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center };
            var p = new TextBox { Width = 120, Watermark = "P_mm" };
            var ce = new TextBox { Width = 80, Watermark = "Ce" };
            var cm = new TextBox { Width = 80, Watermark = "Cm" };
            sp.Children.Add(lbl);
            sp.Children.Add(p);
            sp.Children.Add(ce);
            sp.Children.Add(cm);
            _gridPanel.Children.Add(sp);
            _rows.Add((p, ce, cm));
        }

        private void InitializeComponent() => AvaloniaXamlLoader.Load(this);
    }
}