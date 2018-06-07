#include <zmq.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <sys/types.h>
#include <gst/gst.h>
#include <glib.h>


int main (int argc, char *argv[])
{
    int pid;
    //  Socket to talk to clients
    void *context = zmq_ctx_new ();
    void *responder = zmq_socket (context, ZMQ_REP);
    int rc = zmq_bind (responder, "tcp://*:5500");
    assert (rc == 0);

    int portId=6500;
    char * response = malloc(40*sizeof(char));
    memset(response, 32, 40);

    printf ("Service Dispatcher listening....\n");
    char * buffer = malloc(25*sizeof(char));
    memset(buffer, 0, 25);

    while (1){
        zmq_recv (responder, buffer, 25, 0);
	      sprintf(response, "{\"zmq_port\":%d,\"gst_port\":%d}", portId, portId+1);
        pid = fork();
        if(pid==0){break;}//Pasa a ejecutar el hijo
        zmq_send (responder, response, 40, 0);
        portId=portId+2;
    }
    const char * location = buffer;
    if(pid==0){
      printf("Hijo creado con: %s\n",response);
      GstElement *pipeline;
      GstElement *component;
      GstMessage *msg;
      GstBus *bus;
      GError *error = NULL;

      void *contextChild = zmq_ctx_new ();
      void *responderChild = zmq_socket (contextChild, ZMQ_REP);
      char host [15];
      sprintf(host, "tcp://*:%d", portId);
      printf("%s\n", host);
      int rcChild = zmq_bind (responderChild, host);
      assert (rcChild == 0);

      gst_init (&argc, &argv);

      pipeline = gst_parse_launch ("filesrc name=my_filesrc ! mpegaudioparse ! mpegtsmux ! rtpmp2tpay ! queue max-size-bytes=0 max-size-buffers=0 max-size-time=0 leaky=downstream ! tcpserversink name=my_portsrc host=127.0.0.1", &error);
      if (!pipeline) {
        g_print ("Parse error: %s\n", error->message);
        exit (1);
      }

      component = gst_bin_get_by_name (GST_BIN (pipeline), "my_filesrc");
      g_object_set (component, "location", location, NULL);
      g_object_unref (component);

      component = gst_bin_get_by_name (GST_BIN (pipeline), "my_portsrc");
      g_object_set (component, "port", portId+1, NULL);
      g_object_unref (component);

      gst_element_set_state (pipeline, GST_STATE_PAUSED);

      while(1){
        printf("Waiting a instruction:\n");
        char i_buffered [1];
        zmq_recv (responderChild, i_buffered, 1, 0);
        int i = atoi(i_buffered);
        printf( "You entered: %d\n", i);
        if (i == 0){
          gst_element_set_state (pipeline, GST_STATE_PLAYING);
          zmq_send (responderChild, "playing", 7, 0);
        }
        else if (i == 1){
          gst_element_set_state (pipeline, GST_STATE_PAUSED);
          zmq_send (responderChild, "Paused", 6, 0);
        }
        else if (i == 2){
          zmq_send (responderChild, "Exiting", 7, 0);
          return 0;
        }
        else{
          printf("\nActions: \n  0. Play \n  1. Pause\n  2. Exit\n");
          zmq_send (responderChild, "Showing menu", 12, 0);
        }
      }

      bus = gst_element_get_bus (pipeline);

      /* wait until we either get an EOS or an ERROR message. Note that in a real
       * program you would probably not use gst_bus_poll(), but rather set up an
       * async signal watch on the bus and run a main loop and connect to the
       * bus's signals to catch certain messages or all messages */
      msg = gst_bus_poll (bus, GST_MESSAGE_EOS | GST_MESSAGE_ERROR, -1);

      switch (GST_MESSAGE_TYPE (msg)) {
        case GST_MESSAGE_EOS: {
          g_print ("EOS\n");
          break;
        }
        case GST_MESSAGE_ERROR: {
          GError *err = NULL; /* error to show to users                 */
          gchar *dbg = NULL;  /* additional debug string for developers */

          gst_message_parse_error (msg, &err, &dbg);
          if (err) {
            g_printerr ("ERROR: %s\n", err->message);
            g_error_free (err);
          }
          if (dbg) {
            g_printerr ("[Debug details: %s]\n", dbg);
            g_free (dbg);
          }
        }
        default:
          g_printerr ("Unexpected message of type %d", GST_MESSAGE_TYPE (msg));
          break;
      }
      gst_message_unref (msg);

      gst_element_set_state (pipeline, GST_STATE_NULL);
      gst_object_unref (pipeline);
      gst_object_unref (bus);
      kill(getpid(), SIGKILL);
    }
    else{
      printf("El padre Sale");
    }
    return 0;
}
