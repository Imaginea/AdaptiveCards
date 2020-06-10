/* ----------------------------------------------------------------------------
 * This file was automatically generated by SWIG (http://www.swig.org).
 * Version 4.0.1
 *
 * Do not make changes to this file unless you know what you are doing--modify
 * the SWIG interface file instead.
 * ----------------------------------------------------------------------------- */

package io.adaptivecards.objectmodel;

public class InputsConfig {
  private transient long swigCPtr;
  protected transient boolean swigCMemOwn;

  protected InputsConfig(long cPtr, boolean cMemoryOwn) {
    swigCMemOwn = cMemoryOwn;
    swigCPtr = cPtr;
  }

  protected static long getCPtr(InputsConfig obj) {
    return (obj == null) ? 0 : obj.swigCPtr;
  }

  @SuppressWarnings("deprecation")
  protected void finalize() {
    delete();
  }

  public synchronized void delete() {
    if (swigCPtr != 0) {
      if (swigCMemOwn) {
        swigCMemOwn = false;
        AdaptiveCardObjectModelJNI.delete_InputsConfig(swigCPtr);
      }
      swigCPtr = 0;
    }
  }

  public void setInputLabels(InputLabelsConfig value) {
    AdaptiveCardObjectModelJNI.InputsConfig_inputLabels_set(swigCPtr, this, InputLabelsConfig.getCPtr(value), value);
  }

  public InputLabelsConfig getInputLabels() {
    long cPtr = AdaptiveCardObjectModelJNI.InputsConfig_inputLabels_get(swigCPtr, this);
    return (cPtr == 0) ? null : new InputLabelsConfig(cPtr, false);
  }

  public void setErrorMessage(ErrorMessageConfig value) {
    AdaptiveCardObjectModelJNI.InputsConfig_errorMessage_set(swigCPtr, this, ErrorMessageConfig.getCPtr(value), value);
  }

  public ErrorMessageConfig getErrorMessage() {
    long cPtr = AdaptiveCardObjectModelJNI.InputsConfig_errorMessage_get(swigCPtr, this);
    return (cPtr == 0) ? null : new ErrorMessageConfig(cPtr, false);
  }

  public static InputsConfig Deserialize(JsonValue json, InputsConfig defaultValue) {
    return new InputsConfig(AdaptiveCardObjectModelJNI.InputsConfig_Deserialize(JsonValue.getCPtr(json), json, InputsConfig.getCPtr(defaultValue), defaultValue), true);
  }

  public InputsConfig() {
    this(AdaptiveCardObjectModelJNI.new_InputsConfig(), true);
  }

}
