using System;
using System.Linq;

namespace SAH.Core
{
    /// <summary>
    /// Calculadora hidrológica: funciones Y, Q, V, W del modelo PVCS.
    /// </summary>
    public static class HydrologyCalculator
    {
        /// <summary>
        /// Crea la matriz Y (a x p) a partir de los vectores horarios Ce y Cm.
        /// </summary>
        public static double[,] ComputeYFromHourVectors(double[] ce, double[] cm, int a)
        {
            if (ce == null) throw new ArgumentNullException(nameof(ce));
            if (cm == null) throw new ArgumentNullException(nameof(cm));
            if (a <= 0) throw new ArgumentException("a must be positive", nameof(a));
            if (ce.Length != cm.Length) throw new ArgumentException("ce and cm must have the same length");

            int p = ce.Length;
            double[,] Y = new double[a, p];
            for (int j = 0; j < p; j++)
            {
                double val = ce[j] * cm[j];
                for (int i = 0; i < a; i++)
                {
                    Y[i, j] = val;
                }
            }
            return Y;
        }

        /// <summary>
        /// Calcula la matriz Q = P * Y. P puede estar en mm (unitsMm=true) o en m (unitsMm=false).
        /// </summary>
        public static double[,] ComputeQ(double[] p_mm, double[,] Y, bool unitsMm = true)
        {
            if (p_mm == null) throw new ArgumentNullException(nameof(p_mm));
            if (Y == null) throw new ArgumentNullException(nameof(Y));

            int p = p_mm.Length;
            int a = Y.GetLength(0);
            int py = Y.GetLength(1);
            if (p != py) throw new ArgumentException("Length of P must equal number of columns of Y (p)");

            double[] P = new double[p];
            for (int j = 0; j < p; j++)
            {
                P[j] = unitsMm ? p_mm[j] / 1000.0 : p_mm[j];
            }

            double[,] Q = new double[a, p];
            for (int i = 0; i < a; i++)
            {
                for (int j = 0; j < p; j++)
                {
                    Q[i, j] = P[j] * Y[i, j];
                }
            }
            return Q;
        }

        /// <summary>
        /// Calcula V = A * Q, donde A es un vector de áreas (m²) de longitud a y Q es a x p.
        /// </summary>
        public static double[,] ComputeV(double[] areas_m2, double[,] Q)
        {
            if (areas_m2 == null) throw new ArgumentNullException(nameof(areas_m2));
            if (Q == null) throw new ArgumentNullException(nameof(Q));

            int a = areas_m2.Length;
            int ay = Q.GetLength(0);
            int p = Q.GetLength(1);
            if (a != ay) throw new ArgumentException("Length of A must equal number of rows of Q (a)");

            double[,] V = new double[a, p];
            for (int i = 0; i < a; i++)
            {
                double Ai = areas_m2[i];
                for (int j = 0; j < p; j++)
                {
                    V[i, j] = Ai * Q[i, j];
                }
            }
            return V;
        }

        /// <summary>
        /// Calcula W sumando las antidiagonales de V (convenio: índice k = i + j).
        /// Si V es a x p, W tendrá tamaño h = a + p - 1.
        /// </summary>
        public static double[] ComputeWFromV(double[,] V)
        {
            if (V == null) throw new ArgumentNullException(nameof(V));
            int a = V.GetLength(0);
            int p = V.GetLength(1);
            int h = a + p - 1;
            double[] W = new double[h];
            for (int i = 0; i < a; i++)
            {
                for (int j = 0; j < p; j++)
                {
                    int k = i + j;
                    W[k] += V[i, j];
                }
            }
            return W;
        }

        /// <summary>
        /// Utilidad: convierte un arreglo 2D a string para debugging (no obligatorio).
        /// </summary>
        public static string MatrixToString(double[,] M, int precision = 3)
        {
            if (M == null) return string.Empty;
            int r = M.GetLength(0), c = M.GetLength(1);
            var fmt = "F" + precision;
            return string.Join("\n", Enumerable.Range(0, r).Select(i =>
                string.Join(", ", Enumerable.Range(0, c).Select(j => M[i, j].ToString(fmt)))));
        }
    }
}