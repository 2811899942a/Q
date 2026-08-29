# Guo Fig.2-2 digitized temperature vs V4 NASA POWER forcing

Purpose: determine whether the provisional POWER Tmax/Tmin forcing has a systematic temperature mismatch relative to the same-trial Guo Fig.2-2 curves. Guo Tmax is direct curve extraction; Tmin includes direct black-curve days plus flagged fallback days. Black-only metrics are reported separately.

|Year|Variable|n|Guo mean C|POWER mean C|Guo-POWER bias C|MAE C|RMSE C|r|
|---:|---|---:|---:|---:|---:|---:|---:|---:|
|2019|TMAX|122|31.349|31.463|-0.114|1.373|1.901|0.955|
|2019|TMIN_ALL|121|15.917|18.047|-2.129|5.146|7.312|0.365|
|2019|TMIN_BLACK_ONLY|68|17.484|18.022|-0.538|1.197|1.978|0.937|
|2019|TMEAN_ALL|121|23.689|24.817|-1.128|2.753|3.805|0.775|
|2019|DTR_BLACK_ONLY|68|13.358|13.074|+0.285|1.424|2.258|0.663|
|2020|TMAX|122|31.534|31.654|-0.120|1.353|1.839|0.911|
|2020|TMIN_ALL|121|20.872|18.349|+2.523|3.054|4.832|0.639|
|2020|TMIN_BLACK_ONLY|86|18.639|18.479|+0.161|0.878|1.228|0.943|
|2020|TMEAN_ALL|121|26.239|25.041|+1.198|1.719|2.446|0.843|
|2020|DTR_BLACK_ONLY|86|13.511|13.632|-0.121|1.414|1.871|0.657|

## Extreme-temperature count comparison

- 2019: Tmax>=35 C days, Guo=38 vs POWER=40; on direct-black Tmin days, DTR>=15 C, Guo=14 vs POWER=14.
- 2020: Tmax>=35 C days, Guo=23 vs POWER=31; on direct-black Tmin days, DTR>=15 C, Guo=21 vs POWER=26.

## Interpretation rule

Use this audit to decide whether a Guo-curve temperature substitution diagnostic is warranted. The digitized Fig.2-2 series is an approximate same-trial source, so any crop simulation using it remains a source-reconstruction diagnostic. Rain bars are not used in this temperature comparison because the digitized rain-event total undercaptures the independently reported growing-season precipitation magnitude.
