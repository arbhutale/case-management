import { useEffect, useState, useRef } from "react";
import {
  FormControl,
  Grid,
  Input,
  InputLabel,
  FormHelperText,
  Button,
  Typography,
} from "@material-ui/core";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import TextField from "@mui/material/TextField";
import UploadIcon from "@mui/icons-material/Upload";
import DescriptionIcon from "@mui/icons-material/Description";

import i18n from "../../i18n";
import { IMeeting } from "../../types";
import { useStyles } from "../../utils";
import ProgressBar from "../progressBar/progressBar";

type Props = {
  meeting?: IMeeting;
  readOnly: boolean;
  changed?: boolean;
  setChanged?: any;
  locationError?: boolean;
  notesError?: boolean;
  meetingTypeError?: boolean;
  showUploadButton?: boolean;
  onFileChange?: (event: any, fileDescription: string) => Promise<void>;
  progress?: number;
  showFile?: boolean;
};

const Component = (props: Props) => {
  const classes = useStyles();
  const uploadFileRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [fileDescription, setFileDescription] = useState("");
  const [fileName, setFileName] = useState<string>("");
  const [meeting, setMeeting] = useState<IMeeting>({
    location: "",
    meeting_date: new Date().toISOString().slice(0, 16),
    meeting_type: "",
    legal_case: 0,
    notes: "",
    name: "",
    legal_case_file: null
  });
  console.log(meeting.legal_case_file)

  useEffect(() => {
    if (props.meeting) {
      setMeeting(props.meeting);
    }
  }, [props.meeting]);

  const showOpenFileDialog = () => {
    if (!uploadFileRef.current) throw Error("uploadFileRef is not assigned");
    uploadFileRef.current.click();
  };

  const dialogClose = () => {
    setOpen(false);
    setFileDescription("");
  };

  return (
    <div>
      <Grid
        className={classes.pageBar}
        container
        direction="row"
        spacing={2}
        alignItems="center"
      >
        <Grid item xs={12} md={9}>
          <FormControl fullWidth size="small">
            <InputLabel
              className={classes.inputLabel}
              htmlFor="name"
              shrink={true}
            >
              {i18n.t("Description")}:
            </InputLabel>
            <Input
              id="name"
              disableUnderline={true}
              disabled={props.readOnly}
              className={classes.textField}
              aria-describedby="my-helper-text"
              value={meeting.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setMeeting((meeting) => ({
                  ...meeting,
                  name: e.target.value,
                }));
                props.setChanged(true);
              }}
            />
          </FormControl>
        </Grid>
        {props.showUploadButton && (
          <Grid item className={classes.zeroWidthOnMobile} xs={12} md={3}>
            <input
              ref={uploadFileRef}
              type="file"
              onChange={(event) => {
                if (props.onFileChange) {
                  props.onFileChange(event, fileDescription);
                }

                if (event.target.files) {
                  setFileName(
                    fileDescription.length > 0
                      ? fileDescription
                      : event.target.files[0].name
                  );
                }
              }}
              hidden
            />

            <InputLabel
              className={classes.inputLabel}
              htmlFor="name"
              shrink={true}
            >
              {i18n.t("File")}:
            </InputLabel>
            <Button
              color="primary"
              variant="contained"
              className={classes.meetingFileButton}
              startIcon={<UploadIcon />}
              style={{ textTransform: "none" }}
              onClick={() => setOpen(true)}
            >
              {i18n.t("Upload file")}
            </Button>
            {props.progress
              ? props.progress > 0 && <ProgressBar progress={props.progress} />
              : null}
            {fileName.length > 0 && (
              <FormHelperText id="file-selected">
                File selected:{" "}
                {fileName.length > 28
                  ? fileName.slice(0, 26) + "..."
                  : fileName}
              </FormHelperText>
            )}
            <Dialog open={open} onClose={dialogClose} fullWidth maxWidth="sm">
              <DialogContent>
                <TextField
                  autoFocus
                  margin="dense"
                  id="name"
                  label="File description"
                  type="text"
                  fullWidth
                  variant="standard"
                  value={fileDescription}
                  onChange={(e: React.ChangeEvent<{ value: any }>) => {
                    setFileDescription(e.target.value);
                  }}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={dialogClose}>Cancel</Button>
                <Button
                  color="primary"
                  variant="contained"
                  startIcon={<UploadIcon />}
                  onClick={() => {
                    showOpenFileDialog();
                    setOpen(false);
                  }}
                >
                  {i18n.t("Choose file")}
                </Button>
              </DialogActions>
            </Dialog>
          </Grid>
        )}

        {props.showFile && (
          <Grid xs={12} md={3} >
            <InputLabel
              className={classes.inputLabel}
              htmlFor="name"
              shrink={true}
              style={{paddingLeft:"12px"}}
            >
              {i18n.t("File")}:
            </InputLabel>
            <Grid className={classes.meetingCaseFile}>
              <DescriptionIcon style={{ margin: "0px 15px 0px 10px" }} />
              <Typography>
                <a href={"https://google.com"} target="_blank" rel="noreferrer">
                  {"xxdescription"}
                </a>
              </Typography>
            </Grid>
          </Grid>
        )}

        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel
              className={classes.inputLabel}
              htmlFor="location"
              shrink={true}
            >
              {i18n.t("Location")}:
            </InputLabel>
            <Input
              id="location"
              disableUnderline={true}
              disabled={props.readOnly}
              className={classes.textField}
              aria-describedby="my-helper-text"
              value={meeting.location}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setMeeting((meeting) => ({
                  ...meeting,
                  location: e.target.value,
                }));
                props.setChanged(true);
              }}
            />
            {props.locationError && (
              <FormHelperText error id="location-error">
                Location cannot be empty
              </FormHelperText>
            )}
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel
              className={classes.inputLabel}
              htmlFor="meeting_type"
              shrink={true}
            >
              {i18n.t("Meeting type")}:
            </InputLabel>
            <Input
              id="meeting_type"
              disableUnderline={true}
              disabled={props.readOnly}
              className={classes.textField}
              aria-describedby="my-helper-text"
              value={meeting.meeting_type}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setMeeting((meeting) => ({
                  ...meeting,
                  meeting_type: e.target.value,
                }));
                props.setChanged(true);
              }}
            />
            {props.meetingTypeError && (
              <FormHelperText error id="meeting-type-error">
                Meeting type cannot be empty
              </FormHelperText>
            )}
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel
              className={classes.inputLabel}
              htmlFor="meeting_date"
              shrink={true}
            >
              {i18n.t("Meeting date")}:
            </InputLabel>
            <Input
              id="meeting_date"
              type="datetime-local"
              disableUnderline={true}
              disabled={props.readOnly}
              className={classes.textField}
              aria-describedby="my-helper-text"
              value={new Date(meeting.meeting_date || 0)
                .toISOString()
                .slice(0, 16)}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setMeeting((meeting) => ({
                  ...meeting,
                  meeting_date: e.target.value,
                }));
                props.setChanged(true);
              }}
            />
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth size="small">
            <InputLabel
              className={classes.inputLabel}
              htmlFor="notes"
              shrink={true}
            >
              {i18n.t("Notes")}:{" "}
              {props.notesError && (
                <FormHelperText style={{ fontSize: 16 }} error id="notes-error">
                  Note cannot be empty
                </FormHelperText>
              )}
            </InputLabel>
            <Input
              id="notes"
              multiline
              rows={25}
              style={props.notesError ? { marginTop: 40 } : {}}
              disableUnderline={true}
              disabled={props.readOnly}
              className={classes.textField}
              aria-describedby="my-helper-text"
              value={meeting.notes}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setMeeting((meeting) => ({
                  ...meeting,
                  notes: e.target.value,
                }));
                props.setChanged(true);
              }}
            />
          </FormControl>
        </Grid>
      </Grid>
    </div>
  );
};

Component.defaultProps = {
  readOnly: true,
};

export default Component;
