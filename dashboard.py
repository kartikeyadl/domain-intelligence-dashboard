import streamlit as st
from database import get_dns_data, get_ssl_data
from anomaly import get_all_anomalies
from agent import summarize_anomalies, natural_language_query


st.title("Domain Intelligence Dashboard")

ssl_df = get_ssl_data()
dns_df = get_dns_data()
anomalies = get_all_anomalies()

critical_count = len([a for a in anomalies if a['severity'] == 'CRITICAL'])
warning_count = len([a for a in anomalies if a['severity'] == 'WARNING'])


col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Domains Monitored", len(ssl_df))
with col2:
    st.metric("Critical Issues", critical_count)
with col3:
    st.metric("Warnings", warning_count)

# Natural language query section
st.subheader("Ask a Question")

question = st.text_input(
    "Ask anything about your domains e.g. 'show me domains expiring this month'")

if st.button("Submit"):
    if question:
        with st.spinner("Running query..."):
            df = natural_language_query(question)
        if df.empty:
            st.warning("No results found or query failed.")
        else:
            st.dataframe(df.reset_index(drop=True).rename(lambda x: x+1))
    else:
        st.warning("Please enter a question first.")


st.subheader("SSL Certificates")
st.dataframe(ssl_df[['domain', 'issuer', 'exp_date',
             'days_until_expiry']], hide_index=True)

st.subheader("DNS Records")
st.dataframe(dns_df[['domain', 'record_type', 'value']], hide_index=True)


st.subheader("AI Analysis")

if st.button("Run AI Analysis..."):
    with st.spinner("Analysis anomalies...."):
        summary = summarize_anomalies()

    if summary:
        critical_items = summary.get("critical", [])
        warning_items = summary.get("warning", [])
        info_items = summary.get("info", [])

        if critical_items:
            st.error("**CRITICAL**")
            for item in critical_items:
                st.error(item)

        if warning_items:
            st.warning("**WARNING**")
            for item in warning_items:
                st.warning(item)

        if info_items:
            st.info("**INFO**")
            for item in info_items:
                st.info(item)

    else:
        st.success("No anomalues deteched")
