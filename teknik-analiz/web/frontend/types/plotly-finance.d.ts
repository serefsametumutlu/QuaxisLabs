/** `plotly.js-finance-dist-min` resmi tip paketi (@types) yayınlamıyor —
 * bu proje yalnızca `Plotly.react`/`Plotly.purge`'ı kullandığı için minimal,
 * elle yazılmış bir sözleşme yeterli (tam plotly.js tipleri ~1MB, gereksiz). */
declare module "plotly.js-finance-dist-min" {
  interface Config {
    displayModeBar?: boolean;
    responsive?: boolean;
  }

  interface PlotlyStatic {
    react(
      root: HTMLElement,
      data: unknown[],
      layout?: Record<string, unknown>,
      config?: Config
    ): Promise<unknown>;
    purge(root: HTMLElement): void;
  }

  const Plotly: PlotlyStatic;
  export default Plotly;
}
