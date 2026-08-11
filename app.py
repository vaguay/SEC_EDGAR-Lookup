import requests


class SecEdgar:
    def __init__(self, fileurl):
        self.fileurl = fileurl
        self.name_dict = {}
        self.ticker_dict = {}

        headers = {'user-agent': 'MLT GS agvanesa@gmail.com'}
        response = requests.get(
            self.fileurl,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        # r.json() actually calls the method and returns a dictionary.
        self.filejson = response.json()

        self.cik_json_to_dict()

        #print(r.text)
        #print(self.filejson)



    def cik_json_to_dict(self):
        """
        Convert the SEC ticker JSON into dictionaries for easy lookup.

        ticker_dict:
            "AAPL" -> 320193

        name_dict:
            "APPLE INC." -> 320193
        """
        for company in self.filejson.values():
            cik = company["cik_str"]
            ticker = company["ticker"].upper()
            name = company["title"].upper()

            self.ticker_dict[ticker] = cik
            self.name_dict[name] = cik

    def ticker_to_cik(self, ticker):
        """Return the CIK associated with a stock ticker."""
        ticker = ticker.upper()

        if ticker not in self.ticker_dict:
            raise ValueError(f"Ticker {ticker} was not found.")

        return self.ticker_dict[ticker]



    def _normalize_cik(self, cik):
        """
        Convert a CIK into the 10-digit format required by the SEC API.

        Example:
            320193 -> 0000320193
        """
        cik_string = str(cik).strip()

        if not cik_string.isdigit():
            raise ValueError("CIK must contain only numbers.")

        return cik_string.zfill(10)



#now we:
# 1. ask SEC for the company's filing metadeta
        #parallel arrays: form, filing data, report data, accession number, primary document
# 2. search for correct 10k or 10Q
# 3. Build the URL of the actual filing document
# 4. Return that URL
    def _get_company_filings(self, cik):
        """Ask the SEC for the company's filing metadata."""
        padded_cik = self._normalize_cik(cik)

        url = (
            "https://data.sec.gov/submissions/"
            f"CIK{padded_cik}.json"
        )

        headers = {
            "User-Agent": "MLT GS agvanesa@gmail.com"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    def _build_filing_url(
        self,
        cik,
        accession_number,
        primary_document
        ):
        """Build the URL of the actual filing document."""
        unpadded_cik = str(int(cik))

        accession_without_dashes = accession_number.replace("-", "")

        return (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{unpadded_cik}/"
            f"{accession_without_dashes}/"
            f"{primary_document}"
        )

    def annual_filing(self, cik, year):
        """Return the URL for a company's 10-K for a given year."""
        company_data = self._get_company_filings(cik)

        recent = company_data["filings"]["recent"]

        forms = recent["form"]
        report_dates = recent["reportDate"]
        accession_numbers = recent["accessionNumber"]
        primary_documents = recent["primaryDocument"]

        for i in range(len(forms)):
            form = forms[i]
            report_date = report_dates[i]

            if form == "10-K" and report_date.startswith(str(year)):
                return self._build_filing_url(
                    cik,
                    accession_numbers[i],
                    primary_documents[i]
                )

        raise ValueError(
            f"No 10-K found for CIK {cik} in reporting year {year}."
        )

    def quarterly_filing(self, cik, year, quarter):
        """Return the URL for a company's 10-Q for a given quarter."""
        if quarter not in [1, 2, 3, 4]:
            raise ValueError("Quarter must be between 1 and 4.")

        company_data = self._get_company_filings(cik)

        recent = company_data["filings"]["recent"]

        forms = recent["form"]
        report_dates = recent["reportDate"]
        accession_numbers = recent["accessionNumber"]
        primary_documents = recent["primaryDocument"]

        for i in range(len(forms)):
            form = forms[i]
            report_date = report_dates[i]

            # Some SEC entries have no report date.
            if not report_date or len(report_date) < 7:
                continue

            report_year = int(report_date[:4])
            report_month = int(report_date[5:7])

            report_quarter = ((report_month - 1) // 3) + 1

            if (
                form == "10-Q"
                and report_year == year
                and report_quarter == quarter
            ):
                return self._build_filing_url(
                    cik,
                    accession_numbers[i],
                    primary_documents[i]
                )

        raise ValueError(
            f"No 10-Q found for CIK {cik}, year {year}, "
            f"quarter {quarter}."
        )


se = SecEdgar(
    "https://www.sec.gov/files/company_tickers.json"
)

apple_cik = se.ticker_to_cik("AAPL")

print("Apple CIK:", apple_cik)

print(
    "Annual filing:",
    se.annual_filing(apple_cik, 2024)
)

print(
    "Quarterly filing:",
    se.quarterly_filing(apple_cik, 2024, 2)
)




