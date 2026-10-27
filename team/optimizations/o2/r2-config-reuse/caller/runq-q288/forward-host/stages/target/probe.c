/* Team-owned link probe. Every original or observed host math entry is explicit.
 * This object is inspected, not taken as a numerical or runtime qualification.
 */
extern float powf(float, float);
extern float sinf(float);
extern float cosf(float);
extern void sincosf(float, float *, float *);
extern float expf(float);
extern float sqrtf(float);
extern float roundf(float);
extern double round(double);
extern float fabsf(float);
extern double fabs(double);

volatile float probe_input[2] = {3.25f, 0.5f};
volatile float probe_output[9];
volatile double probe_double_input = 3.25;
volatile double probe_double_output[2];

void probe_math_closure(void) {
    float x = probe_input[0], y = probe_input[1], s, c;
    probe_output[0] = powf(x, y);
    probe_output[1] = sinf(x);
    probe_output[2] = cosf(x);
    sincosf(x, &s, &c);
    probe_output[3] = s;
    probe_output[4] = c;
    probe_output[5] = expf(x);
    probe_output[6] = sqrtf(x);
    probe_output[7] = roundf(x);
    probe_output[8] = fabsf(x);
    probe_double_output[0] = round(probe_double_input);
    probe_double_output[1] = fabs(probe_double_input);
}
