from option_chain import get_option_chain, test_nse_connectivity
from seller_logic import analyze_option_chain
from confidence import confidence_score
from alerts import send_email, should_alert

for symbol in FNO_SYMBOLS:
    df = get_option_chain(symbol)
    alerts = analyze_option_chain(df)

    bias_list = [a["bias"] for a in alerts]
    confidence = confidence_score(bias_list)

    for a in alerts:
        if confidence >= 60 and should_alert(symbol, a["strike"], a["bias"]):
            send_email(
                f"{symbol} Alert",
                f"{symbol} {a['bias']} Strike {a['strike']} Confidence {confidence}%"
            )
