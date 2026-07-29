# ASE-00 damaged-member recovery analysis

- archive SHA-256: `e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`
- archive size: `62601`

## signal_event.json
- expected CRC: `798330cd`
- bad CRC: `d56d2b2b`
- corrected candidate CRC: `798330cd`
- candidate size: `1016` (expected `1016`)
- candidate SHA-256: `22e958d432e588bc4d0c1125706fc42dbdecd587f833f720d23adea46c95c2a7`
- zlib level 0: compressed_size=`1021`, sha256=`d9bcf2dbe1f729256b68b6df4b97332d1d2ab3e2de426a62ede5982945f03a0c`
- zlib level 1: compressed_size=`534`, sha256=`8e725a9ecf10959d438d2bc7a6c8cfe7b13c00bef4bc0d07ed384b8537347f6c`
- zlib level 2: compressed_size=`529`, sha256=`755ef5c9d09a5154d8406e7eb0492f3d244f7408b7c9d651cf3c573de2b8456d`
- zlib level 3: compressed_size=`528`, sha256=`fa7e44f88e3251226d1d907cb2354f060806ea21cde4e86ba54f75e6f8d66ef6`
- zlib level 4: compressed_size=`517`, sha256=`d6abad1b6cf0076665753424615b6b7832c436ab9cdab83418ace38528e8d302`
- zlib level 5: compressed_size=`515`, sha256=`dd0a5524c923a0a26d63c7f81a4873405c50907736a89d3f1935d4c1ec4ef3a2`
- zlib level 6: compressed_size=`515`, sha256=`dd0a5524c923a0a26d63c7f81a4873405c50907736a89d3f1935d4c1ec4ef3a2`
- zlib level 7: compressed_size=`515`, sha256=`dd0a5524c923a0a26d63c7f81a4873405c50907736a89d3f1935d4c1ec4ef3a2`
- zlib level 8: compressed_size=`515`, sha256=`dd0a5524c923a0a26d63c7f81a4873405c50907736a89d3f1935d4c1ec4ef3a2`
- zlib level 9: compressed_size=`515`, sha256=`dd0a5524c923a0a26d63c7f81a4873405c50907736a89d3f1935d4c1ec4ef3a2`

## momentum.py
- expected CRC: `4cda9409`
- expected size: `3548`
- compressed size: `1124`
- raw compressed SHA-256: `38323b323881676fb949f77572e02759739eba83fb26cc79dec2449593d93625`
- decompressed size: `3536`
- bad CRC: `f6b2a2d3`
- bad SHA-256: `36a76aabed80d4372e7bb6effa3a73a80cb5b4d91bcc8781961c45e81c2cffb6`

### Decompressed momentum.py
```python

from __future__ import annotations

import numpy as np
import pandas as pd

from strategy_engine.features.common import rma, safe_divide, source_series


def rsi(close: pd.Series, period: int = 14, ma_type: str = "rma") -> pd.Series:
    if period < 2:
        raise ValueError("period must be >= 2")
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    if ma_type == "rma":
        average_gain = rma(gains, period)
        average_loss = rma(losses, period)
    elif ma_type == "sma":
        average_gain = gains.rolling(period, min_periods=period).mean()
        average_loss = losses.rolling(period, min_periods=period).mean()
    else:
        raise ValueError("ma_type must be 'rma' or 'sma'")

    rs = safe_divide(average_gain, average_loss)
    result = 100.0 - 100.0 / (1.0 + rs)
    result = result.mask((average_gain == 0.0) & (average_loss == 0.0), 50.0)
    result = result.mask((average_loss == 0.0) & (average_gain > 0.0), 100.0)
    result = result.mask((average_gain == 0.0) & (average_loss > 0.0), 0.0)
    return result


def stochastic_rsi(
    close: pd.Series,
    *,
    rsi_period: int = 14,
    stochastic_period: int = 14,
    k_smoothing: int = 3,
    d_smoothing: int = 3,
    rsi_(n,k((average_n r_'ataFrame-> pd.Sering(
    *,
  ,nt = 14,
    stoch,nt = 14,
   ,int = 3,
   )   1n()
    else:
        raise all rma(losrror("period1must be
   v    )
  ries


d, 
    *,
  ,nnt = 3,
   ust be
s = lo) &w)
  ri v    oss = lost = 14,
    stoch,ning(period, t = 14,
    stochrioi=period)
s = lo)high)
  ri v    oss = lost = 14,
    stoch,ning(period, t = 14,
    stochrioaxperiod)
aw)
    res*")

    rs = 
   v    )-e
s = lo) &w,)
s = lo)high)-e
s = lo) &weriod)k)
  awoss = lost = 14,
   ,iing(period, t = 14,
   riods=period)d)
 koss = losd = 14,
   ,iing(period, d = 14,
   riods=period)), 0.0) r_'ataFrame({"
  ":  ri v    ,f m = 1_
  ":  aw,f m = 1_
  _k": k,f m = 1_
  _d": d})ource_sepd
_of_ 14ngees


def rsi(close: pd.Series, per2 str = "rma") -> pd.Series:
    1n()
    else:
        raise ValueError("period1must be
, 0.0)   res*"()

    rs = s


d,     deshiftsses.ro))sultss >urce_sw ==trend_tegy_engochastframe-) r_'ataFramee: pd.Series, 14nnel_lom thries, per0eries, == 0.0) om thries, pe21od: intignal_lom thries, peiod: intfe_di rsi_(n,khl2"eries, orttant: floa, pe re15erage_n r_'ataFrame-> pd."""Independes, W ==Trend-style oscillatst fst engearch.' or 'This is a genes.c public-fstmulaturelemes,impor, __  a parity   aim fst Miyagi.> pd."""> pd.Sering( 14nnel_lom th,, == 0.0) om th,ntignal_lom th)   1n()
    else:
        raise rma(losrror("period1must beSer orttant <pe n()
    else:
        raise  orttant ror("peri 0must besrca'")fe_divide, s(frame safe_dieriod).s2")
src.ewm(ss n= 14nnel_lom th,, djor(=Fal
d, ing(period,  14nnel_lom thriods=period)deviimpor")
(srca-).s2).abs().ewm(()
    elss n= 14nnel_lom th,, djor(=Fal
d, ing(period,  14nnel_lom th()
  riods=period) 14nnel_indexa'")

    rs = srca-).s2,r orttant *)deviimporeriod)wt1")
 14nnel_index.ewm(ss n= == 0.0) om th,n djor(=Fal
d, ing(period,  == 0.0) om thriods=period)wt2")
wt1oss = lostignal_lom th,ning(period, tignal_lom th)iods=period)),00.0)
  r_'ataFrame(index=frame.indexeriod)),00.0["w ==trend"]")
wt1riod)),00.0["w ==trend_tignal"]")
wt2riod)),00.0["w ==trend_  los"]")
wt1a-)wt2riod)),00.0["w ==trend_cr& (_up"]")
(wt1a>)wt2_gainwt1oshifts1) <pewt2oshifts1)eriod)),00.0["w ==trend_cr& (_down"]")
(wt1a<)wt2_gainwt1oshifts1) >pewt2oshifts1)eriod)), 0.0)
    re
```

### momentum.py repr
```text
b'\nfrom __future__ import annotations\n\nimport numpy as np\nimport pandas as pd\n\nfrom strategy_engine.features.common import rma, safe_divide, source_series\n\n\ndef rsi(close: pd.Series, period: int = 14, ma_type: str = "rma") -> pd.Series:\n    if period < 2:\n        raise ValueError("period must be >= 2")\n    delta = close.diff()\n    gains = delta.clip(lower=0.0)\n    losses = -delta.clip(upper=0.0)\n    if ma_type == "rma":\n        average_gain = rma(gains, period)\n        average_loss = rma(losses, period)\n    elif ma_type == "sma":\n        average_gain = gains.rolling(period, min_periods=period).mean()\n        average_loss = losses.rolling(period, min_periods=period).mean()\n    else:\n        raise ValueError("ma_type must be \'rma\' or \'sma\'")\n\n    rs = safe_divide(average_gain, average_loss)\n    result = 100.0 - 100.0 / (1.0 + rs)\n    result = result.mask((average_gain == 0.0) & (average_loss == 0.0), 50.0)\n    result = result.mask((average_loss == 0.0) & (average_gain > 0.0), 100.0)\n    result = result.mask((average_gain == 0.0) & (average_loss > 0.0), 0.0)\n    return result\n\n\ndef stochastic_rsi(\n    close: pd.Series,\n    *,\n    rsi_period: int = 14,\n    stochastic_period: int = 14,\n    k_smoothing: int = 3,\n    d_smoothing: int = 3,\n    rsi_(n,k((average_n r_\'ataFrame-> pd.Sering(\n    *,\n  ,nt = 14,\n    stoch,nt = 14,\n   ,int = 3,\n   )   1n()\n    else:\n        raise all rma(losrror("period1must be\n   v    )\n  ries\n\n\nd, \n    *,\n  ,nnt = 3,\n   ust be\ns = lo) &w)\n  ri v    oss = lost = 14,\n    stoch,ning(period, t = 14,\n    stochrioi=period)\ns = lo)high)\n  ri v    oss = lost = 14,\n    stoch,ning(period, t = 14,\n    stochrioaxperiod)\naw)\n    res*")\n\n    rs = \n   v    )-e\ns = lo) &w,)\ns = lo)high)-e\ns = lo) &weriod)k)\n  awoss = lost = 14,\n   ,iing(period, t = 14,\n   riods=period)d)\n koss = losd = 14,\n   ,iing(period, d = 14,\n   riods=period)), 0.0) r_\'ataFrame({"\n  ":  ri v    ,f m = 1_\n  ":  aw,f m = 1_\n  _k": k,f m = 1_\n  _d": d})ource_sepd\n_of_ 14ngees\n\n\ndef rsi(close: pd.Series, per2 str = "rma") -> pd.Series:\n    1n()\n    else:\n        raise ValueError("period1must be\n, 0.0)   res*"()\n\n    rs = s\n\n\nd,     deshiftsses.ro))sultss >urce_sw ==trend_tegy_engochastframe-) r_\'ataFramee: pd.Series, 14nnel_lom thries, per0eries, == 0.0) om thries, pe21od: intignal_lom thries, peiod: intfe_di rsi_(n,khl2"eries, orttant: floa, pe re15erage_n r_\'ataFrame-> pd."""Independes, W ==Trend-style oscillatst fst engearch.\' or \'This is a genes.c public-fstmulaturelemes,impor, __  a parity   aim fst Miyagi.> pd."""> pd.Sering( 14nnel_lom th,, == 0.0) om th,ntignal_lom th)   1n()\n    else:\n        raise rma(losrror("period1must beSer orttant <pe n()\n    else:\n        raise  orttant ror("peri 0must besrca\'")fe_divide, s(frame safe_dieriod).s2")\nsrc.ewm(ss n= 14nnel_lom th,, djor(=Fal\nd, ing(period,  14nnel_lom thriods=period)deviimpor")\n(srca-).s2).abs().ewm(()\n    elss n= 14nnel_lom th,, djor(=Fal\nd, ing(period,  14nnel_lom th()\n  riods=period) 14nnel_indexa\'")\n\n    rs = srca-).s2,r orttant *)deviimporeriod)wt1")\n 14nnel_index.ewm(ss n= == 0.0) om th,n djor(=Fal\nd, ing(period,  == 0.0) om thriods=period)wt2")\nwt1oss = lostignal_lom th,ning(period, tignal_lom th)iods=period)),00.0)\n  r_\'ataFrame(index=frame.indexeriod)),00.0["w ==trend"]")\nwt1riod)),00.0["w ==trend_tignal"]")\nwt2riod)),00.0["w ==trend_  los"]")\nwt1a-)wt2riod)),00.0["w ==trend_cr& (_up"]")\n(wt1a>)wt2_gainwt1oshifts1) <pewt2oshifts1)eriod)),00.0["w ==trend_cr& (_down"]")\n(wt1a<)wt2_gainwt1oshifts1) >pewt2oshifts1)eriod)), 0.0)\n    re'
```

### One-byte CRC recovery candidates
- none
- original CRC repeated: `f6b2a2d3`

## test_squeeze.py
- expected CRC: `cd127679`
- expected size: `1150`
- expected compressed size: `451`
- branch candidate CRC: `cd127679`
- branch candidate size: `1150`
- branch candidate SHA-256: `b1a86115a0c628bda7cda9ded441460759dcc44bbcb766e63600312039a7ff4b`
- damaged raw compressed SHA-256: `e0bc3e33950215710c1df9e75e3b5839cf3126d283bd584c2307bccc7b22b9dc`
- zlib level 0: compressed_size=`1155`, sha256=`a1be2618829ba4f30493564195afc674cf32692b46d103f2d4ff8206c5b730bc`
- zlib level 1: compressed_size=`455`, sha256=`98906dba935423f129976693468bcbabaea098828dd0caa9f55fc3a0a2152ec4`
- zlib level 2: compressed_size=`455`, sha256=`12c784c56d3ecc619f8b25f493bb6363ab8f95b3ed5016639cc5ab413229f7cf`
- zlib level 3: compressed_size=`454`, sha256=`317b1ab5b68c36c266d8249c8e6a45c1ab1c00f8589f9670ad5b4bb4dd4ce6d9`
- zlib level 4: compressed_size=`451`, sha256=`0c011d5e580628e6ad124cb3c1479d151ac8b8ab15b80f36d1a1cfb113e35d0e`
- zlib level 5: compressed_size=`451`, sha256=`0c011d5e580628e6ad124cb3c1479d151ac8b8ab15b80f36d1a1cfb113e35d0e`
- zlib level 6: compressed_size=`451`, sha256=`0c011d5e580628e6ad124cb3c1479d151ac8b8ab15b80f36d1a1cfb113e35d0e`
- zlib level 7: compressed_size=`451`, sha256=`0c011d5e580628e6ad124cb3c1479d151ac8b8ab15b80f36d1a1cfb113e35d0e`
- zlib level 8: compressed_size=`451`, sha256=`0c011d5e580628e6ad124cb3c1479d151ac8b8ab15b80f36d1a1cfb113e35d0e`
- zlib level 9: compressed_size=`451`, sha256=`0c011d5e580628e6ad124cb3c1479d151ac8b8ab15b80f36d1a1cfb113e35d0e`
