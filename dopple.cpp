#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>

#include "timer.h"

#define NUM_TIME_SLICES			2500
#define  TMP_FMT_SIZE			1024
#define TMP_LABEL_SIZE			8
#define BUFFER_SIZE				67108848
#define READ_CHUNK_SIZE			8388608

#define SIZE_B  8e0
#define SIZE_KB 1024.
#define SIZE_MB 1.0e6
#define SIZE_GB 1.0e9
#define SIZE_TB 1.0e12
#define SIZE_PB 1.0e15

#define LABEL_B  "B"
#define LABEL_KB "KB"
#define LABEL_MB "MB"
#define LABEL_GB "GB"
#define LABEL_TB "TB"
#define LABEL_PB "PB"

typedef enum {
	CHUNK_UNKNOWN,
	CHUNK_READ,
	CHUNK_WRITE,
	CHUNK_IDLE,
	CHUNK_WAIT,
	NUM_CHUNK_TYPES
} chunk_t;

typedef struct copy_chunk_t {
	chunk_t	type;
	double	time_slice;
	long	data_size;
} copy_chunk_t;

copy_chunk_t g_time_slices[NUM_TIME_SLICES];
int g_time_slice_idx = 0;

typedef struct opts_t {
	char*	src_filename;
	char*	dst_filename;
	int seq;
	int rand;
	int noreuse;
	int dontneed;
	int willneed;
	int chunk_size;
} opts_t;

opts_t g_opts;

void init_time_array()
{
//	memset(g_time_slices, 0, sizeof(copy_chunk_t) * NUM_TIME_SLICES);
	for ( int i = 0; i < NUM_TIME_SLICES; i++ ) {
		g_time_slices[i].type = CHUNK_UNKNOWN;
		g_time_slices[i].time_slice = 0.0f;
		g_time_slices[i].data_size = 0;
	}

	g_time_slice_idx = 0;
}

void add_time_slice(chunk_t type, double slice, long data_size)
{
	if ( g_time_slice_idx < NUM_TIME_SLICES ) {
		if ( type < NUM_CHUNK_TYPES ) {
			g_time_slices[g_time_slice_idx].type = type;
		}
		g_time_slices[g_time_slice_idx].time_slice = slice;
		g_time_slices[g_time_slice_idx++].data_size = data_size;
	} else {
		fprintf(stderr, "[%s] Unable to add, array full\n", __func__);
	}
}

void print_time_slices(FILE* outfile)
{
	for ( int i = 0; i < g_time_slice_idx; i++ ) {
		fprintf(outfile, "%d: %d %.04f %lu\n", i, g_time_slices[i].type, g_time_slices[i].time_slice, g_time_slices[i].data_size);
//		fprintf(stderr, "%d: %d %.04f %lu\n", i, g_time_slices[i].type, g_time_slices[i].time_slice, g_time_slices[i].data_size);
	}
}


/*
 * double get_scale
 * - takes the transfer size and an allocated label string
 * - returns: the ratio to scale the transfer size to be human readable
 * - state  : writes the label for the scale to char*label
 */

double get_scale(off_t size, char*label, int label_size)
{
	char    tmpLabel[TMP_LABEL_SIZE];
	double  tmpSize = 1.0;

	if (size < SIZE_KB){
		snprintf(tmpLabel, TMP_LABEL_SIZE - 1, LABEL_B);
		tmpSize = SIZE_B;
	} else if (size < SIZE_MB){
		snprintf(tmpLabel, TMP_LABEL_SIZE - 1, LABEL_KB);
		tmpSize = SIZE_KB;
	} else if (size < SIZE_GB){
		snprintf(tmpLabel, TMP_LABEL_SIZE - 1, LABEL_MB);
		tmpSize = SIZE_MB;
	} else if (size < SIZE_TB){
		snprintf(tmpLabel, TMP_LABEL_SIZE - 1, LABEL_GB);
		tmpSize = SIZE_GB;
	} else if (size < SIZE_PB){
		snprintf(tmpLabel, TMP_LABEL_SIZE - 1, LABEL_TB);
		tmpSize = SIZE_TB;
	} else {
		snprintf(tmpLabel, TMP_LABEL_SIZE - 1, LABEL_PB);
		tmpSize = SIZE_PB;
	}

	snprintf(label, label_size - 1, "%s", tmpLabel);
//	fprintf(stderr, "get_scale: size = %ld, label = %s, newSize = %f\n", size, label, tmpSize);
//	label = "[?]";
	return tmpSize;
}

/*
 * int print_progress
 * - prints the fraction of data transfered for the current file with a carriage return
 * - returns: RET_SUCCESS on success, RET_FAILURE on failure
 */

int print_progress(char* descrip, off_t read, off_t total)
{
	char label[TMP_LABEL_SIZE];
	char fmt[TMP_FMT_SIZE];
	int path_width = 60;

	// Get the width of the terminal
	struct winsize term;
	if (!ioctl(fileno(stdout), TIOCGWINSZ, &term)){
		int progress_width = 35;
		path_width = term.ws_col - progress_width;
	}

	// Scale the amount read and generate label
	off_t ref = (total > read) ? total : read;
	double scale = get_scale(ref, label, TMP_LABEL_SIZE);

	// if we know the file size, print percentage of completion
	if (total) {
		double percent = total ? read*100./total : 0.0;
		snprintf(fmt, TMP_FMT_SIZE - 1, "\r +++ %%-%ds %%0.2f/%%0.2f %%s [ %%.2f %%%% ]", path_width);
		fprintf(stderr, fmt, descrip, read/scale, total/scale, label, percent);
//		fprintf(stderr, "\n");

	} else {
		snprintf(fmt, TMP_FMT_SIZE - 1, "\r +++ %%-%ds %%0.2f/? %%s [ ? %%%% ]", path_width);
		fprintf(stderr, fmt, descrip, read/scale, label);
//		fprintf(stderr, "\n");
	}

	return 0;
}

/*
 * void print_xfer_stats
 * - prints the average speed, total data transfered, and time of transfer to terminal
 */
void print_xfer_stats(double elapsed_time, off_t total_transferred)
{
	char label[TMP_LABEL_SIZE];

	double scale = get_scale(total_transferred, label, TMP_LABEL_SIZE);

	fprintf(stderr, "\n\tSTAT: %.2f %s transfered in %.2fs [ %.2f Gbps ] \n",
			total_transferred/scale, label, elapsed_time,
			total_transferred/(elapsed_time*SIZE_GB));
}

// Get the size of a file, should handle large files as well
off_t fsize(int fd)
{
	struct stat tmp_stat;
	fstat(fd, &tmp_stat);
	return tmp_stat.st_size;
}

//int test_file_copy()
int test_file_copy(char* source_filename, char* dest_filename, int posix_advice_seq, int posix_advice_use, int read_chunk_size)
{
	int read_mode = O_LARGEFILE | O_RDONLY;
	int write_mode = O_LARGEFILE | O_WRONLY | O_TRUNC | O_CREAT;
	char* buffer;
	int read_file, write_file;
	int rs = 1, files_verified = 0;
	off_t sent = 0, temp_sent = 0, read_file_size = 0, write_file_size = 0;
	int read_chunk_timer = 0, write_chunk_timer = 0, total_timer = 0;

	buffer = (char*)malloc(sizeof(char) * BUFFER_SIZE);

	read_chunk_timer = new_timer("read_chunk_timer");
	write_chunk_timer = new_timer("write_chunk_timer");
	total_timer = new_timer("total_timer");

	// open the existing file
	read_file = open(source_filename, read_mode);
	// open the target location
	write_file = open(dest_filename, write_mode, S_IRUSR | S_IWUSR);

	if ( (read_file != -1) & (write_file != -1) ) {
		// get the file size
		read_file_size = fsize(read_file);

		// set posix info
		posix_fadvise64(read_file, 0, 0, posix_advice_seq | posix_advice_use);

		start_timer(total_timer);
		while (rs) {
//		while ((rs = read(fd, sender_block.data, BUFFER_LEN))) {
//			fprintf(stderr, "Starting timer\n");
			start_timer(read_chunk_timer);
			int temp_read = 0;
			int bytes_remaining = BUFFER_SIZE;
			int byte_count_to_read;
			while ( bytes_remaining && rs ) {
				if ( bytes_remaining < read_chunk_size ) {
					byte_count_to_read = bytes_remaining;
				} else {
					byte_count_to_read = read_chunk_size;
				}
				rs = read(read_file, buffer + temp_read, byte_count_to_read);
//				fprintf(stderr, "Read %d bytes\n", rs);
				temp_read += rs;
				bytes_remaining -= rs;
			}
			stop_timer(read_chunk_timer);
			double read_elapsed = timer_elapsed(read_chunk_timer);

			// Check for file read error
			if (rs < 0) {
				fprintf(stderr, "Error reading from file: %d\n", errno);
			}

			start_timer(write_chunk_timer);
			temp_sent = write(write_file, buffer, temp_read);
			if ( temp_sent == -1 ) {
				fprintf(stderr, "error writing, code %d - %s\n", errno, strerror(errno));
			}
			stop_timer(write_chunk_timer);
			sent += temp_sent;
			double write_elapsed = timer_elapsed(write_chunk_timer);

			add_time_slice(CHUNK_READ, read_elapsed, temp_read);
			add_time_slice(CHUNK_WRITE, write_elapsed, temp_sent);

			// Print progress
			print_progress(dest_filename, sent, read_file_size);
//			fprintf(stderr, "\n");
		}
	} else {
		fprintf(stderr, "write_file = %d, read_file = %d\n", write_file, read_file);
		if (write_file == -1) {
			fprintf(stderr, "Unable to open file %s for writing - %s\n", dest_filename, strerror(errno));
		} else {
			fprintf(stderr, "Unable to open file %s for reading - %s\n", source_filename, strerror(errno));
		}
	}
	stop_timer(total_timer);
	double elapsed = timer_elapsed(total_timer);
	write_file_size = fsize(write_file);
	print_xfer_stats(elapsed, write_file_size);
	files_verified = (write_file_size == read_file_size);
	close(read_file);
	close(write_file);
	free(buffer);
	fprintf(stdout, "\n");

	return files_verified;
}

void usage(int EXIT_STAT)
{

	char* options[] = {
		"-h       \t print this message",
		"-f       \t filename of file to use",
		"-c       \t read chunk size (in bytes, defaults to 8388608)",
		"-r/-s    \t (r)andom or (s)equential (sequential is default)",
		"-n/-w/-d \t (n)oreuse, (w)illneed, or (d)ontneed (noreuse is default)",
		NULL
	};

	fprintf(stderr, "Basic usage: \n\tcopy_test [file_to_copy] [options]\n");
	fprintf(stderr, "Options:\n");

	for (int i = 0; options[i]; i++)
		fprintf(stderr, "   %s\n", options[i]);

	exit(EXIT_STAT);

}

void parse_options(int argc, char *argv[])
{
	int tmp_size;

	if ( argc > 1 ) {
		int opt;

		// Read in options
		while ((opt = getopt(argc, argv, "f:c:rsnwdh")) != -1) {
	//		fprintf(stderr, "opt = %c\n", opt);
			switch (opt) {
				// file name of file to copy
				case 'f':
				{
					int total_len = strlen(optarg);
					int new_len = (sizeof(char) * (total_len + 5));
					g_opts.dst_filename = (char*)malloc(new_len);
					g_opts.src_filename = strdup(optarg);
					memset(g_opts.dst_filename, 0, new_len);
					snprintf(g_opts.dst_filename, new_len - 1, "%s-tmp", optarg);
					break;
				}

				case 'c':
					tmp_size = atoi(optarg);
					if ( (tmp_size > 0) && (tmp_size <= 67108848) ) {
						g_opts.chunk_size = atoi(optarg);
					} else {
						fprintf(stdout, "Invalid chunk_size: %d, defaulting to %d\n", tmp_size, READ_CHUNK_SIZE);
					}
					break;
				case 'r':
					g_opts.seq = 0;
					g_opts.rand = 1;
					break;
				case 's':
					g_opts.seq = 1;
					g_opts.rand = 0;
					break;
				case 'n':
					g_opts.noreuse = 1;
					g_opts.dontneed = 0;
					g_opts.willneed = 0;
					break;
				case 'w':
					g_opts.noreuse = 0;
					g_opts.dontneed = 0;
					g_opts.willneed = 1;
					break;
				case 'd':
					g_opts.noreuse = 0;
					g_opts.dontneed = 1;
					g_opts.willneed = 0;
					break;
				case 'h':
					usage(0);
					break;

				default:
					fprintf(stderr, "Unknown command line option: [%c].\n", opt);
					usage(0);
					break;
			}
		}

	} else {
		fprintf(stderr, "Too few arguments\n");
		usage(0);
	}

}

char* create_log_filename()
{
//	fprintf(stderr, "Creating filename\n");
	char* out_filename = NULL;
	char tmp_flag_str[64];
	time_t cur_time = time(NULL);
	tm* cur_tm = localtime((const time_t*)&cur_time);

	// filename: nameStr-dateStamp-opts.log
	memset(tmp_flag_str, 0, sizeof(char) * 64);

	if (g_opts.seq ){
		strncat(tmp_flag_str, "seq_", 4);
	} else {
		strncat(tmp_flag_str, "rnd_", 4);
	}
	if ( g_opts.noreuse ) {
		strncat(tmp_flag_str, "nore", 4);
	}else if ( g_opts.dontneed ) {
		strncat(tmp_flag_str, "dont", 4);
	} else {
		strncat(tmp_flag_str, "will", 4);
	}

	out_filename = (char*)malloc(sizeof(char) * 128);
//	fprintf(stderr, "flag_str = %s\n", tmp_flag_str);
	sprintf(out_filename, "copyLog_%02d-%02d-%04d_%02d-%02d-%02d_%s.log",
		cur_tm->tm_mon + 1, cur_tm->tm_mday, cur_tm->tm_year + 1900,
		cur_tm->tm_hour, cur_tm->tm_min, cur_tm->tm_sec, tmp_flag_str);
//	fprintf(stderr, "out_filename = %s\n", out_filename);

	return out_filename;
}


int main(int argc, char *argv[])
{
	int result;
	FILE* log_file;
	char* log_filename;

	g_opts.src_filename = NULL;
	g_opts.dst_filename = NULL;
	g_opts.seq = 1;
	g_opts.rand = 0;
	g_opts.noreuse = 1;
	g_opts.dontneed = 0;
	g_opts.willneed = 0;
	g_opts.chunk_size = READ_CHUNK_SIZE;

/*	int test_advice[6] = {
		POSIX_FADV_SEQUENTIAL | POSIX_FADV_NOREUSE,
		POSIX_FADV_SEQUENTIAL | POSIX_FADV_DONTNEED,
		POSIX_FADV_SEQUENTIAL | POSIX_FADV_WILLNEED,
		POSIX_FADV_RANDOM | POSIX_FADV_NOREUSE,
		POSIX_FADV_RANDOM | POSIX_FADV_DONTNEED,
		POSIX_FADV_RANDOM | POSIX_FADV_WILLNEED,
	}; */

	parse_options(argc, argv);

	// get the filename from the args
	if ( argc > 1 ) {
/*		int total_len = strlen(argv[1]);
		int new_len = (sizeof(char) * (total_len + 5));
		dest_filename = (char*)malloc(new_len);
		src_filename = strdup(argv[1]);
		int array_size = sizeof(test_advice) / sizeof(int);
		for ( file_count = 0; file_count < array_size; file_count++ ) {
			init_time_array();
			memset(dest_filename, 0, new_len);
			snprintf(dest_filename, new_len - 1, "%s-%02d", argv[1], file_count);
			result = test_file_copy(src_filename, dest_filename, test_advice[file_count]);
			if ( result ) {
				fprintf(stderr, "Files identical\n");
			} else {
				fprintf(stderr, "Files different\n");
			}
			print_time_slices();
			fprintf(stderr, "Removing %s\n", dest_filename);
			remove(dest_filename);
		}
		memset(dest_filename, 0, new_len);
		snprintf(dest_filename, new_len - 1, "%s-%02d", argv[1], file_count); */
		result = test_file_copy(g_opts.src_filename, g_opts.dst_filename,
			g_opts.seq | g_opts.rand,
			g_opts.noreuse | g_opts.dontneed | g_opts.willneed, READ_CHUNK_SIZE);
		if ( result ) {
			fprintf(stderr, "Files identical\n");
		} else {
			fprintf(stderr, "Files different\n");
		}
		log_filename = create_log_filename();
		log_file = fopen(log_filename, "w+");
		print_time_slices(log_file);
		fclose(log_file);
		fprintf(stdout, "%s\n", log_filename);
		free(log_filename);
//		fprintf(stderr, "Removing %s\n", g_opts.dst_filename);
		remove(g_opts.dst_filename);

	} else {
		fprintf(stderr, "Please give me a file name to copy\n");
	}
	return 0;
}