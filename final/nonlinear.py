import csv
import matplotlib.pyplot as plt
import numpy as np

frequencies = [
    {'freq': 10,
        'file_path' : './square_tri/RigolDS100.csv',
        'fall_edge_start' : -0.2,
        'fall_edge_end':    -0.15,
        'rise_edge_start':  0.15,
        'rise_edge_end' :   0.2},
    {'freq': 1100,
        'file_path' : './square_tri/sqtrik10.csv',
        'fall_edge_start' : -(3.93/1100)/2,
        'fall_edge_end':    -(2.93/1100)/2,
        'rise_edge_start':  (2.93/1100)/2,
        'rise_edge_end' :   (3.93/1100)/2},
    {'freq': 10000,
        'file_path' : './square_tri/sqtrik100.csv',
        'fall_edge_start' : -(3.93/10000)/2,
        'fall_edge_end':    -(2.93/10000)/2,
        'rise_edge_start':  (3.15/10000)/2,
        'rise_edge_end' :   (3.97/10000)/2}
]
def show_non_linearity(freq,file_path, fall_edge_start, fall_edge_end, rise_edge_start, rise_edge_end):
    print(fall_edge_start)
    print(fall_edge_end)

    csv_file = file_path
    time = []
    ch2v = []

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            time.append(float(row['Time(s)']))
            ch2v.append(float(row['CH2V']))

    time = np.array(time)
    ch2v = np.array(ch2v)
    # Get the falling edge and rising edge portions of the wave
    fall_edge_mask = (time >= fall_edge_start) & (time <=  fall_edge_end)
    rise_edge_mask = (time >= rise_edge_start) & (time <=  rise_edge_end)

    fall_time_seg = time[fall_edge_mask]
    fall_ch2v_seg = ch2v[fall_edge_mask]

    rise_time_seg = time[rise_edge_mask]
    rise_ch2v_seg = ch2v[rise_edge_mask]

    # Generate the lines of best fit and R^2 values for both edges
    fall_slope, fall_inter = np.polyfit(fall_time_seg, fall_ch2v_seg, 1)
    fall_fit_line = fall_slope * fall_time_seg + fall_inter
    fall_residuals = fall_ch2v_seg - fall_fit_line
    fall_ss_res = np.sum(fall_residuals**2)
    fall_ss_tot = np.sum((fall_ch2v_seg - np.mean(fall_ch2v_seg))**2)
    fall_r_squared = 1 - (fall_ss_res / fall_ss_tot)

    rise_slope, rise_inter = np.polyfit(rise_time_seg, rise_ch2v_seg, 1)
    rise_fit_line = rise_slope * rise_time_seg + rise_inter
    rise_residuals = rise_ch2v_seg - rise_fit_line
    rise_ss_res = np.sum(rise_residuals**2)
    rise_ss_tot = np.sum((rise_ch2v_seg - np.mean(rise_ch2v_seg))**2)
    rise_r_squared = 1 - (rise_ss_res / rise_ss_tot)

    # Plot full waveform
    plt.plot(time, ch2v, label='Waveform')
    # Plot lines of best fit
    plt.plot(fall_time_seg, fall_fit_line, 'r--', label='Falling edge linear fit')
    plt.plot(rise_time_seg, rise_fit_line, 'g--', label='Rising edge linear fit')

    # Add annotation text
    fall_equation_text = f'y = {fall_slope:.3f}x + {fall_inter:.3f}\n$R^2$ = {fall_r_squared:.4f}'
    rise_equation_text = f'y = {rise_slope:.3f}x + {rise_inter:.3f}\n$R^2$ = {rise_r_squared:.4f}'

    plt.text(fall_time_seg[0], max(fall_ch2v_seg), fall_equation_text,
            fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))

    plt.text(rise_time_seg[0], max(rise_ch2v_seg)/2, rise_equation_text,
            fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))

    # Plot settings
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.title(f'{freq}Hz triangle wave linear fit on rising and falling edges ')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    for frequency in frequencies:
        show_non_linearity(frequency['freq'], frequency['file_path'], frequency['fall_edge_start'],frequency['fall_edge_end'], frequency['rise_edge_start'], frequency['rise_edge_end'])

if __name__ == "__main__":
    main()