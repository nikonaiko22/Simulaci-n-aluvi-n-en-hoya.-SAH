using System;
using Xunit;
using SAH.Core;

namespace SAH.Tests
{
    public class HydrologyCalculatorTests
    {
        [Fact]
        public void ComputeYFromHourVectors_Basic()
        {
            double[] ce = { 0.5, 0.6 };
            double[] cm = { 1.0, 1.0 };
            var Y = HydrologyCalculator.ComputeYFromHourVectors(ce, cm, 2);
            Assert.Equal(2, Y.GetLength(0));
            Assert.Equal(2, Y.GetLength(1));
            Assert.Equal(0.5, Y[0, 0], 6);
            Assert.Equal(0.6, Y[0, 1], 6);
        }

        [Fact]
        public void ComputeWFromV_Antidiagonals()
        {
            double[,] V = new double[,]
            {
                { 1, 2 },
                { 3, 4 }
            };
            var W = HydrologyCalculator.ComputeWFromV(V);
            // a=2, p=2 => h=3
            Assert.Equal(3, W.Length);
            Assert.Equal(1, W[0], 6);        // i=0,j=0
            Assert.Equal(2 + 3, W[1], 6);    // (0,1)+(1,0)
            Assert.Equal(4, W[2], 6);        // (1,1)
        }
    }
}