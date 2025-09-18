from flask import Flask, render_template, request
import csv
import re
import io

app = Flask(__name__)
pattern_1 = re.compile(r'appConfig.s4lgcConfig.routes\[(\d+)U\]\.distEntryExitSignal')
pattern_2=re.compile(r'appConfig.s4lgcConfig.routes\[(\d+)U\]\.ssp\.speedInfo\[(\d+)U\]\.dist')
pattern_3=re.compile(r'appConfig.s4lgcConfig.routes\[(\d+)U\]\.entrySigTagId')
my_dict={
    1:(16,pattern_1),
    2:(34,pattern_2),
    3:(15,pattern_3)
}

# def load_csv1(file):
#     reader = csv.reader(io.StringIO(file.read().decode('utf-8')))
#     rows = list(reader)

#     headers = rows[0]
#     valid_headers = [(i, h.strip()) for i, h in enumerate(headers) if h.strip()]
#     header_indices = {name: idx for idx, name in valid_headers}

#     cleaned_data = []
#     for row in rows[1:]:
#         if not row or not row[0].strip().isdigit():
#             continue
#         data = {name: row[idx].strip() if idx < len(row) else '' for name, idx in header_indices.items()}
#         cleaned_data.append(data)
#     print(cleaned_data)
#     return cleaned_data


def load_csv1(file):
    reader = csv.reader(io.StringIO(file.read().decode('utf-8')))
    rows = list(reader)

    headers = rows[0]
    # Mapping column indices to the actual headers (no filtering)
    header_indices = {idx: h.strip() for idx, h in enumerate(headers)}
    # valid_headers = [(i, h.strip()) for i, h in enumerate(headers) if h.strip()]
    # header_indices = {i: idx for i, (idx, _) in enumerate(valid_headers)}

    cleaned_data = []
    for row in rows[1:]:
        if not row or not row[0].strip().isdigit():
            continue
        
        # Create a list of values based on the column indices
        data = [row[idx].strip() if idx < len(row) else '' for idx in range(len(headers))]
        
        # Append the list to the cleaned_data list
        cleaned_data.append(data)
    
    return cleaned_data

def load_csv2_1(file,pattern):
    mapping = {}

    reader = csv.reader(io.StringIO(file.read().decode('utf-8')))
    for idx,row in enumerate(reader):
        if len(row) < 4:
            continue
        
        match = pattern.search(row[0])
        if match:
            print('matched')
            sno = int(match.group(1)) + 1
            try:
                value = float(row[3].strip())
                if sno in mapping:
                    mapping[sno] = (mapping[sno][0], mapping[sno][1] + value)  # (idx+1, sum of values)
                else:
                    mapping[sno] = (idx + 1, value)
            except ValueError:
                pass
    print(mapping)
    return mapping


def load_csv2_2(file, pattern):
    mapping = {}
    reader = list(csv.reader(io.StringIO(file.read().decode('utf-8'))))

    i = 0
    while i < len(reader):
        row = reader[i]
        if len(row) < 4:
            i += 1
            continue

        match = pattern.search(row[0])
        if match:
            sno = int(match.group(1)) + 1
            sub_pattern_1 = re.compile(rf'appConfig.s4lgcConfig.routes\[{sno-1}U\]\.enRouteTags\[(\d+)U\]\.linkDistance')
            sub_pattern_2=re.compile(rf'appConfig.s4lgcConfig.routes\[{sno-1}U\]\.enRouteTags\[(\d+)U\]\.tagId')
            # scan next rows until mismatch
            j = i + 2
            while j < len(reader):
                row2 = reader[j]
                sub_match_1 = sub_pattern_1.search(row2[0])
                sub_match_2 = sub_pattern_2.search(reader[j+1][0])
                if not  sub_match_1 or not sub_match_2:
                    break   # stop at first non-matching row

                #tag_idx = int(sub_match_1.group(1))
                value=row2[3]
                id=reader[j+1][3]
                if id=='0':
                    break
                if sno in mapping:
                    mapping[sno][0].append(j+1)
                    mapping[sno][1].append(value)
                    mapping[sno][2].append(id)
                else:
                    mapping[sno] = ([j+1], [value],[id])
                j += 2

            # skip ahead
            i = j
        else:
            i += 1
    return mapping


def compare_data_2(csv1_data, csv2_data, column_index):
    results = []

    for row in csv1_data:
        try:
            sno = int(row[0])  # Get S.No from the first column
            csv1_val = row[column_index].strip()
            csv1_val = csv1_val.split(")#(")


            line_no, dist, id = csv2_data.get(sno, ([], [], []))  # Use empty lists if not found

            for i in range(len(csv1_val)):
                csv1_value = csv1_val[i].replace('(', '').replace(')', '')
                csv1_parts = csv1_value.split('#')

                csv1_item_1 = csv1_parts[0] if len(csv1_parts) > 0 else 'Invalid'
                csv1_item_2 = csv1_parts[1] if len(csv1_parts) > 0 else 'Invalid'
                # Default values if index out of range
                index_val = line_no[i] if i < len(line_no) else 'Missing'
                dist_val = dist[i] if i < len(dist) else 'Missing'
                id_val=id[i] if i < len(id) else 'Missing'

                # Determine match status
                if i < len(dist) and dist[i] is not None:
                    match_status = 'Match' if csv1_item_1 == dist[i] else 'Mismatch'
                else:
                    match_status = 'Missing'

                results.append({
                    'S.No': sno,
                    'CSV1_Dist': csv1_item_1,
                    'CSV1_RFID':csv1_item_2,
                    'Index': index_val,
                    'CSV2_Dist': dist_val,
                    'CSV2_RFID':id_val,
                    'Status': match_status
                })
        except Exception as e:
            print(f"Exception: {e}")
            pass
    return results


def compare_data(csv1_data, csv2_data, column_index):
    results = []
    for row in csv1_data:
        try:
            sno = int(row[0])  # Get S.No from the first column
            csv1_val = float(row[column_index].strip()) if row[column_index].strip() else 0.0
            index, csv2_val = csv2_data.get(sno, (None, None))
            
            match_status = 'Match' if csv2_val == csv1_val else 'Mismatch'
            results.append({
                'S.No': sno,
                'CSV1_Value': csv1_val,
                'Index': index,
                'CSV2_Value': csv2_val if csv2_val is not None else 'Not Found',
                'Status': match_status if csv2_val is not None else 'Missing in CSV2'
            })
        except (ValueError, KeyError, IndexError):  # Handle missing or incorrect data
            results.append({
                'S.No': row[0] if len(row) > 0 else 'Unknown',  # Assuming 'S.No' is in the first column
                'CSV1_Value': row[column_index] if len(row) > column_index else 'Invalid',  # Handle invalid data
                'CSV2_Value': 'Error',
                'Status': 'Error'
            })
    return results


def compare_data_3(csv1_data, csv2_data_1,csv2_data_2,column_index):
    results = []
    for row in csv1_data:
        try:
            sno = int(row[0])  # Get S.No from the first column
            csv1_val = float(row[column_index].strip()) if row[column_index].strip() else 0.0
            index_1, csv2_val_1 = csv2_data_1.get(sno, (None, None))
            index_2, csv2_val_2 = csv2_data_2.get(sno, (None, None))
            match_status = 'Match' if (csv2_val_1 == csv1_val) and  (csv2_val_1 == csv2_val_2) else 'Mismatch'
            results.append({
                'S.No': sno,
                'CSV1_Value': csv1_val,
                'Index_1': index_1,
                'CSV2_Value_1': csv2_val_1 if csv2_val_1 is not None else 'Not Found',
                'Index_2':index_2,
                'CSV2_Value_2': csv2_val_2 if csv2_val_2 is not None else 'Not Found',
                'Status': match_status if csv2_val_1 is not None else 'Missing in CSV2'
            })
        except (ValueError, KeyError, IndexError):  # Handle missing or incorrect data
            results.append({
                'S.No': row[0] if len(row) > 0 else 'Unknown',  # Assuming 'S.No' is in the first column
                'CSV1_Value': row[column_index] if len(row) > column_index else 'Invalid',  # Handle invalid data
                'CSV2_Value': 'Error',
                'Status': 'Error'
            })
    return results


# def compare_data(csv1_data, csv2_data, column_index):
#     results = []
#     for row in csv1_data:
#         try:
#             # sno = int(row['S.No'])
#             # csv1_val = float(row.get(column_name, '').strip())
#             # Assuming 'S.No' is at index 0 in each row
#             sno = int(row[0])  # Get S.No from the first column
#             csv1_val = float(row[column_index].strip()) if row[column_index].strip() else 0.0
#             index,csv2_val = csv2_data.get(sno)
#             match_status = 'Match' if csv2_val == csv1_val else 'Mismatch'
#             results.append({
#                 'S.No': sno,
#                 'CSV1_Value': csv1_val,
#                 'Index':index,
#                 'CSV2_Value': csv2_val if csv2_val is not None else 'Not Found',
#                 'Status': match_status if csv2_val is not None else 'Missing in CSV2'
#             })
#         except (ValueError, KeyError):
#             results.append({
#                 'S.No': row.get('S.No', 'Unknown'),
#                 'CSV1_Value': row.get(column_index, 'Invalid'),
#                 'CSV2_Value': 'Error',
#                 'Status': 'Error'
#             })
#     return results

@app.route('/', methods=['GET', 'POST'])
def index():
    result_data = []
    if request.method == 'POST':
        csv1_file = request.files.get('csv1_file')
        csv2_file = request.files.get('csv2_file')
        selected_value = request.form.get('selected')
        value = my_dict[int(selected_value)]
        column_index,pattern=value
        if csv1_file and csv2_file:
            try:
                csv1_data = load_csv1(csv1_file)
                if (selected_value=="3"):

                    csv2_data = load_csv2_2(csv2_file,pattern)
                    result_data = compare_data_2(csv1_data, csv2_data,column_index)
                elif (selected_value=="2"):
                    Span_pattern=re.compile(r'appConfig.aggrProfConfiguration.trackProf\[(\d+)U\]\.profSpan')
                    csv2_data_1 = load_csv2_1(csv2_file,pattern)
                    csv2_file.seek(0)
                    csv2_data_2 = load_csv2_1(csv2_file,Span_pattern)
                    result_data = compare_data_3(csv1_data, csv2_data_1,csv2_data_2,column_index)
                else:

                    csv2_data = load_csv2_1(csv2_file,pattern)
                    result_data = compare_data(csv1_data, csv2_data,column_index)
            except Exception as e:
                return render_template('index.html', error=str(e), result_data=[])
    return render_template('index.html', result_data=result_data)

if __name__ == '__main__':
    app.run(debug=True)
