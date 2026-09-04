"""Action-potential biomarker extraction for spontaneously active SAN models.

Definitions follow Fabbri et al. 2017 (J Physiol 595:2365-2396), Table 5:

  CL      cycle length, peak-to-peak interval               [ms]
  MDP     maximum diastolic potential (most negative V)     [mV]
  OS      overshoot (peak V)                                [mV]
  APA     action potential amplitude, OS - MDP              [mV]
  DDR100  diastolic depolarization rate over the FIRST      [mV/s]
          100 ms of diastolic depolarization, i.e. starting
          at MDP: (V(t_MDP + 100ms) - V(t_MDP)) / 100ms
  dVdtmax maximum rate of rise of membrane potential        [V/s]

The model's native time unit is seconds; biomarkers are returned in the units
above to match the published table.
"""
import numpy as np

DDR_WINDOW_S = 0.100          # 100 ms, per the DDR100 definition


def find_peaks(t, v, min_peak_mv=-10.0, min_sep_s=0.150):
    """Indices of AP peaks: local maxima above min_peak_mv, separated in time."""
    peaks = []
    for i in range(1, len(v) - 1):
        if v[i] >= v[i - 1] and v[i] > v[i + 1] and v[i] > min_peak_mv:
            if peaks and (t[i] - t[peaks[-1]]) < min_sep_s:
                if v[i] > v[peaks[-1]]:
                    peaks[-1] = i
                continue
            peaks.append(i)
    return np.array(peaks, dtype=int)


def biomarkers(t, v, require_beats=3):
    """Compute biomarkers from a logged trace. Returns dict, or None if the
    trace does not contain enough complete beats (i.e. not spontaneously
    firing). Never raises on a quiescent trace - the caller decides."""
    t = np.asarray(t, dtype=float)
    v = np.asarray(v, dtype=float)

    peaks = find_peaks(t, v)
    if len(peaks) < require_beats:
        return None

    # Use complete cycles only: drop first and last partial cycles.
    cls, mdps, oss, ddrs, dvdts = [], [], [], [], []
    for k in range(len(peaks) - 1):
        i0, i1 = peaks[k], peaks[k + 1]
        cl_s = t[i1] - t[i0]

        # MDP within this cycle
        seg = slice(i0, i1 + 1)
        j = i0 + int(np.argmin(v[seg]))
        mdp = v[j]

        # DDR100: 100 ms window starting at MDP
        t_end = t[j] + DDR_WINDOW_S
        if t_end <= t[i1]:
            v_end = np.interp(t_end, t, v)
            ddrs.append((v_end - mdp) / DDR_WINDOW_S)   # mV/s

        # dV/dt max on the upstroke (from MDP to next peak)
        up = slice(j, i1 + 1)
        if up.stop - up.start > 2:
            dv = np.diff(v[up]) / np.diff(t[up])        # mV/s
            dvdts.append(np.max(dv) / 1000.0)           # V/s

        cls.append(cl_s * 1000.0)                       # ms
        mdps.append(mdp)
        oss.append(v[i1])

    if not cls:
        return None

    return {
        "n_beats": len(cls),
        "CL_ms": float(np.mean(cls)),
        "CL_ms_sd": float(np.std(cls)),
        "MDP_mV": float(np.mean(mdps)),
        "OS_mV": float(np.mean(oss)),
        "APA_mV": float(np.mean(oss) - np.mean(mdps)),
        "DDR100_mV_s": float(np.mean(ddrs)) if ddrs else float("nan"),
        "dVdtmax_V_s": float(np.mean(dvdts)) if dvdts else float("nan"),
    }
