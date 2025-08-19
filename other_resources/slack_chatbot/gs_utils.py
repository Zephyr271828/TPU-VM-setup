# first we do a google sheet util
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = ""
SAMPLE_RANGE_NAME = "VAE-VAE:[flops]"


def convert_column_to_int(column: str) -> int:
    """
    for example, 'A' -> 1, 'AA' -> 28, 'AB' -> 29, 'BA' -> 55
    """
    sum = 0
    for i in reversed(range(len(column))):
        sum += sum * 27 + ord(column[i]) - ord("A") + 1
    return sum


def convert_int_to_column(num: int) -> str:
    """
    for example, 1 -> 'A', 28 -> 'AA', 29 -> 'AB', 55 -> 'BA'
    """
    column = ""
    while num > 0:
        column = chr(num % 27 - 1 + ord("A")) + column
        num = num // 27
    return column


def get_valid_column(st_column: str, length: int) -> str:
    """
    for example, 'A' + 27 = 'AA', 'A' + 27 + 1 = 'AB', 'AB' + 27 = 'BB'
    """
    st_colum_int = convert_column_to_int(st_column)
    end_column_int = st_colum_int + length

    end_colum_str = convert_int_to_column(end_column_int)
    print(
        f"[INFO] Get valid column from {st_column}: {st_colum_int} + {length} = {end_column_int} -> {end_colum_str}"
    )
    return end_colum_str


def init_googleapi_credentials(json_dir_path: str):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_json_path = os.path.join(json_dir_path, "tokens.json")
    if os.path.isfile(token_json_path):
        creds = Credentials.from_authorized_user_file(token_json_path, SCOPES)
        print(f"[INFO] Load credentials from {token_json_path}")
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print("[INFO] No valid credentials found. Please login.")
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cred_path = os.path.join(json_dir_path, "gs_credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_json_path, "w") as token:
            token.write(creds.to_json())
    return creds


from typing import List, Tuple
from googleapiclient.discovery import build


class TPU_Usage:
    def __init__(self):
        self.user_list = []  # user names
        self.usage_list = []  # usage in cores
        self.tpu_belonging = {}  # "user_name": [("tpu_name", "tpu_cores")]

    def add_user(self, user: str):
        self.user_list.append(user)
        self.usage_list.append(0)
        self.tpu_belonging[user] = []

    def update_usage(self, user: str, tpu_list: List[Tuple[str, int]]):
        if user not in self.user_list:
            self.add_user(user)
        idx = self.user_list.index(user)
        self.tpu_belonging[user] = tpu_list
        self.usage_list[idx] = sum([tpu[1] for tpu in tpu_list])

    def __str__(self):
        message = ""
        for user, core in zip(self.user_list, self.usage_list):
            message += f"{user}: {core} cores\n"
            for tpu in self.tpu_belonging[user]:
                message += f"  {tpu[0]}: {tpu[1]} cores\n"
        return message

    def refresh(self):
        # clear all
        self.user_list = []
        self.usage_list = []
        self.tpu_belonging = {}

    def _pad_columns(
        self, user_list: List[str], usage_list: List[int], tpu_belonging: dict
    ) -> Tuple[List[str], List[int], List[str]]:
        """
        Pad the user_list and usage_list so that they have the same length as the longest TPU list.
        """
        padded_user_list = []
        padded_usage_list = []
        tpu_names = []
        tpu_cores = []
        for user in user_list:
            tpus = tpu_belonging[user]
            num_tpus = len(tpus)
            # Pad user and usage with empty strings or zeros to match the length of tpus
            padded_user_list.extend([user] + [""] * (num_tpus - 1))
            padded_usage_list.extend(
                [usage_list[user_list.index(user)]] + [""] * (num_tpus - 1)
            )
            tpu_names.extend([tpu[0] for tpu in tpus])
            tpu_cores.extend([tpu[1] for tpu in tpus])
        return padded_user_list, padded_usage_list, tpu_names, tpu_cores

    def return_formatted_data(self) -> List[List[str]]:
        """
        Return a Google Sheets formatted list:
        First column: user name (merged down)
        Second column: usage in cores (merged down)
        Third column: TPU names
        """
        formatted_list = []

        # Pad the first two columns to match the length of the TPU names
        padded_user_list, padded_usage_list, tpu_names, tpu_cores = self._pad_columns(
            self.user_list, self.usage_list, self.tpu_belonging
        )

        # Construct the formatted data
        for i, user in enumerate(padded_user_list):
            formatted_list.append(
                [padded_user_list[i], padded_usage_list[i], tpu_names[i], tpu_cores[i]]
            )

        return formatted_list

    def merge_cells_for_users(self, service, spreadsheet_id: str):
        """
        Merge cells in the first two columns for each user.
        """
        requests = []
        current_row = 2  # Start from row 2 in the sheet

        for i, user in enumerate(self.user_list):
            tpus = self.tpu_belonging[user]
            num_tpus = len(tpus)
            #print(
            #    f"[INFO] Merging cells for {user} at row {current_row} to {current_row + num_tpus-1}"
            #)
            # Merge user name and usage cells in the first two columns
            requests.extend(
                [
                    {
                        "mergeCells": {
                            "range": {
                                "sheetId": 0,  # Assuming the first sheet, modify if necessary
                                "startRowIndex": current_row - 1,  # Row index 0-based
                                "endRowIndex": current_row + num_tpus - 1,
                                "startColumnIndex": 0,  # Column A
                                "endColumnIndex": 1,  # Column B
                            },
                            "mergeType": "MERGE_ALL",
                        }
                    },
                    {
                        "mergeCells": {
                            "range": {
                                "sheetId": 0,  # Assuming the first sheet, modify if necessary
                                "startRowIndex": current_row - 1,  # Row index 0-based
                                "endRowIndex": current_row + num_tpus - 1,
                                "startColumnIndex": 1,  # Column A
                                "endColumnIndex": 2,  # Column B
                            },
                            "mergeType": "MERGE_ALL",
                        }
                    },
                ]
            )
            current_row += num_tpus  # Move to the next set of rows for the next user
        # Define the range to apply the vertical alignment (entire column A)
        alignment_range = {
            "sheetId": 0,
            "startRowIndex": 1,  # Starting from the first row
            "endRowIndex": 100,  # Adjust as needed; this example covers 1000 rows
            "startColumnIndex": 0,  # Column A (0-indexed)
            "endColumnIndex": 4,  # Column A (0-indexed)
        }
        bold_range = {
            "sheetId": 0,
            "startRowIndex": 1,  # Starting from the first row
            "endRowIndex": 100,  # Adjust as needed; this example covers 1000 rows
            "startColumnIndex": 0,  # Column A (0-indexed)
            "endColumnIndex": 2,  # Column A (0-indexed)
        }
        # Create the request to update the vertical alignment
        update_cells_request = {
            "repeatCell": {
                "range": alignment_range,
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)",
            }
        }
        # Create the request to update the bold formatting
        bold_request = {
            "repeatCell": {
                "range": bold_range,
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {
                            "bold": True
                        }
                    }
                },
                "fields": "userEnteredFormat.textFormat.bold"
            }
        }

        requests.append(update_cells_request)
        requests.append(bold_request)
        # Perform the batch update to merge cells
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()


# Example Usage:
def init_gsheet_service(cred_dir: str):
    creds = init_googleapi_credentials(cred_dir)
    service = build("sheets", "v4", credentials=creds)
    return service


def upload_data_to_spreadsheet(
    formatted_data: List[List[str]], service, spreadsheet_id: str, Sheetname: str
):
    # automatically set range, starts from A2 (left-up)
    total_length = len(formatted_data)
    column_length = len(formatted_data[0])
    end_column = convert_int_to_column(column_length)
    range_ = f"{Sheetname}!A2:{end_column}{total_length+1}"
    #print(f"[INFO] Uploading data to {spreadsheet_id} at {range_}")
    body = {"values": formatted_data}
    # first clear out all the data in the columns
    clear_range_ = f"{Sheetname}!A2:{end_column}"
    clear_body = {
        "range": clear_range_,
    }
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id, range=clear_range_, body=clear_body
    ).execute()
    # unmerge every cell in the range, use proper google sheet api, there is no unmerge() function
    unmerge_body = {
        "range": {
            "sheetId": 0,
        }
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"unmergeCells": unmerge_body}]},
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_, valueInputOption="RAW", body=body
    ).execute()
    #print(f"[INFO] Data uploaded to {spreadsheet_id} at {range_}")


def main():
    # Define the Google Sheets API service
    creds = init_googleapi_credentials("./")
    service = build("sheets", "v4", credentials=creds)

    # Spreadsheet ID of your Google Sheet
    spreadsheet_id = ""

    # Initialize TPU_Usage instance
    tpu_usage = TPU_Usage()

    # Add some users and their TPU usage
    tpu_usage.update_usage("user1", [("tpu1", 4), ("tpu2", 5), ("tpujapan", 114514)])
    tpu_usage.update_usage("user2", [("tpu3", 3), ("tpujapan", 114514)])

    # Get the formatted data ready for upload
    formatted_data = tpu_usage.return_formatted_data()
    #print(formatted_data)

    # Upload the data to Google Sheets
    upload_data_to_spreadsheet(formatted_data, service, spreadsheet_id, "TPU_Usage")

    # Merge cells in Google Sheets for each user
    tpu_usage.merge_cells_for_users(service, spreadsheet_id)


if __name__ == "__main__":
    main()


class GoogleSheet_Bot:
    def __init__(
        self,
        spreadsheet_id: str,
        sheet_id: str,
        start_range: str,
        creds: Credentials = None,
        value_input_option: str = "USER_ENTERED",
    ):
        if not creds or not creds.valid:
            print("[INFO] No valid credentials provided. Try load from token.json.")
            creds = init_googleapi_credentials()
        self.creds = creds
        self.service = build("sheets", "v4", credentials=creds)
        self.spreadsheet_id = spreadsheet_id
        self.range_column = start_range[0]
        self.value_input_option = value_input_option
        assert self.range_column.isalpha()
        self.sheet_id = sheet_id
        self.range_row = start_range[1]
        assert self.range_row.isdigit()
        print(
            f"[INFO] Google API service created with spreadsheet_id: {spreadsheet_id}, start_range: {start_range}"
        )

    def update_to_googlesheet(self):
        for key in self.attr_dict.keys():
            _values = self.attr_dict[key]
            if _values is None:
                continue
            body = {"values": _values}
            length = len(_values)
            max_depth = len(_values[0])
            end_column = get_valid_column(self.range_column, max_depth + 1)
            end_row = int(self.range_row) + length + 1
            range_name = f"{self.sheet_id}!{self.range_column}{self.range_row}:{end_column}{end_row}"
            self.range_row = end_row + 1
            #print(f"[INFO] Updating {key} to {self.sheet_id}!{range_name}")
            try:
                result = (
                    self.service.spreadsheets()
                    .values()
                    .update(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name,
                        valueInputOption=self.value_input_option,
                        body=body,
                    )
                    .execute()
                )
            except HttpError as error:
                print(f"An error occurred when updating {key}: {error}")
                return error
        #print("[INFO] Update finished.")
