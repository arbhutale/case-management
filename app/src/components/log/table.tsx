import React, { useEffect } from "react";
import { useHistory } from "react-router-dom";
import SearchIcon from "@material-ui/icons/Search";

import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Avatar from "@mui/material/Avatar";

import {
  Divider,
  Grid,
  IconButton,
  Input,
  InputAdornment,
  InputLabel,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
} from "@material-ui/core";
import List from "@mui/material/List";
import { useStyles } from "../../utils";
import i18n from "../../i18n";
import { format } from "date-fns";
import { getLegalCases, getClients } from "../../api";
import { ILegalCase, IClient, ILog } from "../../types";

const LogLabels = new Map([
  ['LegalCase Create', 'Case created'],
  ['LegalCase Update', 'Case update'],
  ['Meeting Create', 'New meeting'],
  ['Meeting Update', 'Meeting updated'],
  ['LegalCaseFile Create', 'File uploaded'],
  ['LegalCaseFile Update', 'File updated']
]);

const logLabel = (targetAction:string | undefined, targetType: string | undefined) => {
  return LogLabels.get(`${targetType} ${targetAction}`);
};

type Props = {
  logs: ILog[];
  standalone: boolean;
};

const Component = (props: Props) => {
  const history = useHistory();
  const classes = useStyles();
  const [clients, setClients] = React.useState<IClient[]>();
  const [legalCases, setLegalCases] = React.useState<ILegalCase[]>();
  const [filteredLogs, setfilteredLogs] = React.useState<ILog[]>();
  const [filterLogsValue, setfilterLogsValue] = React.useState<string>();

  const filterKeyUp = (event: React.KeyboardEvent<HTMLInputElement>) => {
    filterLogs();
  };

  //TODO: Better filtering
  const filterLogs = () => {
    if (filterLogsValue) {
      setfilteredLogs(
        props.logs.filter((log) => {
          return (
            log.action.toLowerCase().includes(filterLogsValue.toLowerCase()) ||
            log.note?.toLowerCase().includes(filterLogsValue.toLowerCase()) ||
            log.target_type
              .toLowerCase()
              .includes(filterLogsValue.toLowerCase())
          );
        })
      );
    } else {
      setfilteredLogs(props.logs);
    }
  };

  useEffect(() => {
    if (props.logs.length > 0 && typeof filteredLogs === "undefined") {
      filterLogs();
    }
  });

  useEffect(() => {
    async function fetchData() {
      const dataClients = await getClients();
      const dataLegalCases = await getLegalCases();
      setLegalCases(dataLegalCases);
      setClients(dataClients);
    }
    fetchData();
  }, []);

  return (
    <div>
      <Grid container direction="row" spacing={2} alignItems="center">
        <Grid item style={{ flexGrow: 1 }}>
          <strong>
            {filteredLogs ? filteredLogs.length : "0"} {i18n.t("Logs")}
          </strong>
        </Grid>
        <Grid item>
          <InputLabel
            className={classes.inputLabel}
            htmlFor="sort_table"
            shrink={true}
          >
            {i18n.t("Sort")}:
          </InputLabel>
        </Grid>
        <Grid item>
          <Select
            id="sort_table"
            className={classes.select}
            disableUnderline
            input={<Input />}
            value="alphabetical"
          >
            <MenuItem key="alphabetical" value="alphabetical">
              {i18n.t("Alphabetical")}
            </MenuItem>
          </Select>
        </Grid>
        <Grid item md={12}>
          <Input
            id="table_search"
            fullWidth
            placeholder={i18n.t("Search updates...")}
            startAdornment={
              <InputAdornment position="start">
                <IconButton>
                  <SearchIcon color="primary" />
                </IconButton>
              </InputAdornment>
            }
            disableUnderline={true}
            className={classes.textField}
            aria-describedby="my-helper-text"
            value={filterLogsValue}
            onChange={(e) => setfilterLogsValue(e.target.value)}
            onKeyUp={filterKeyUp}
          />
        </Grid>
      </Grid>
      <List sx={{ width: "100%", marginBottom: "26px" }}>
          <Divider />
          {filteredLogs ? filteredLogs
                ?.slice(0)
                .reverse()
                .map((item) => (
                  <>
                    <ListItem className={classes.caseHistoryList}>
                      <Chip
                        label={logLabel(item.action, item.target_type)}
                        className={classes.chip}
                      />
                      <ListItemText
                        primary={
                          <Typography variant="caption">{item.note}</Typography>
                        }
                        style={{ flexGrow: 1 }}
                      />
                      <ListItemAvatar sx={{ minWidth: 40 }}>
                        <Avatar
                          alt="Paul Watson"
                          src="/static/images/avatar/1.jpg"
                          className={classes.caseHistoryAvatar}
                          sx={{ width: 28, height: 28 }}
                        />
                      </ListItemAvatar>
                      <Typography sx={{ fontSize: "11px", color: "#616161" }}>
                        {format(new Date(item?.created_at!), "MMM dd, yyyy")}
                      </Typography>
                    </ListItem>
                    <Divider />
                  </>
                ))
            : ""}
        </List>
    </div>
  );
};

Component.defaultProps = {
  standalone: true,
};

export default Component;
