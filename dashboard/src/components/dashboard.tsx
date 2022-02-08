import i18next from "i18next";
import React from "react";
import Grid from "@material-ui/core/Grid";
import { createStyles, Theme, makeStyles } from "@material-ui/core/styles";
import Container from "@material-ui/core/Container";
import Typography from "@material-ui/core/Typography";
import FormControl from "@material-ui/core/FormControl";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import Box from "@mui/material/Box";
import BarChartIcon from "@mui/icons-material/BarChart";

import Layout from "../components/layout";
import BarChart from "../components/bar-chart";
import HeatmapChart from "../components/heatmap-chart";
import {
  IDbDataByRange,
  IDbDataMonthly,
  IDbDataDailyPerMonth,
  IBarChart,
  IHeatmapChart,
} from "../types";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    header: {
      backgroundColor: theme.palette.primary.main,
      color: theme.palette.secondary.main,
      padding: "1.5rem",
    },
    headerContainer: {
      display: "flex",
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      [theme.breakpoints.down("sm")]: {
        flexDirection: "column",
        alignItems: "flex-start",
        padding: "0.5rem 0",
      },
    },
    pageHeader: {
      backgroundColor: "#ffffff",
      padding: "1.5rem",
      marginBottom: "16px",
      boxShadow: "0px 4px 5px 0px rgba(0, 0, 0, 0.05)",
      [theme.breakpoints.down("sm")]: {
        padding: "1.5rem 0",
      },
    },
    title: {
      fontSize: "20px",
      fontWeight: "bold",
      [theme.breakpoints.down("sm")]: {
        paddingBottom: "16px",
      },
    },
    secondTitle: {
      fontSize: "20px",
      fontWeight: "bold",
      paddingLeft: "1rem",
    },
    headerSelect: {
      minWidth: "10rem",
      backgroundColor: "#ffffff",
      border: "solid 1px #f2f2f2",
      borderRadius: "4px",
      padding: "8px 8px 4px 8px",
      "&.Mui-disabled": {
        backgroundColor: "rgba(0, 0, 0, 0.05)",
        color: "#000000",
        "&>.MuiSelect-icon": {
          display: "none",
        },
      },
      "&.Mui-focused": {
        backgroundColor: "#fcfcfc",
        borderColor: "#e5e5e5",
      },
      "&:hover": {
        backgroundColor: "#e5e5e5",
      },
    },
    iconAndTitle: {
      display: "flex",
      flexDirection: "row",
      alignItems: "center",
    },
    dropdownStyle: {
      marginTop: "3rem",
    },
    dataGrid: {
      width: "inherit",
    },
  })
);

interface IProps {
  dataByRange: IDbDataByRange;
  dataMonthly: IDbDataMonthly;
  dataDaily: IDbDataDailyPerMonth;
}

export default function Dashboard(props: IProps) {
  const classes = useStyles();

  const generateChartData = (): Array<IBarChart | IHeatmapChart> => {
    const charts: Array<IBarChart | IHeatmapChart> = [];
    const barChartMetrics = [
      "Active case officers",
      "Total cases",
      "Average cases per officer",
      "Average days per case",
      "Cases opened",
      "Cases closed",
    ];
    barChartMetrics.forEach((name: string) => {
      charts.push({
        type: "bar",
        metric: name,
        dataMonthly: props.dataMonthly,
        dataByRange: props.dataByRange,
      });
    });
    charts.push({
      type: "heatmap",
      data: props.dataDaily,
      metrics: ["Cases opened", "Cases closed", "Cases with activity"],
    });
    return charts;
  };

  const [state, setState] = React.useState({
    selectedOffice: "",
    charts: generateChartData(),
  });

  const updateOffice = (office: string) => {
    const charts: Array<IBarChart | IHeatmapChart> = generateChartData();
    setState({
      ...state,
      charts,
      selectedOffice: office,
    });
  };

  const offices = Object.keys({
    ...props.dataMonthly.dataPerCaseOffice,
    ...props.dataDaily.dataPerCaseOffice,
  });

  if (state.selectedOffice === "" && offices.length) {
    updateOffice(offices[0]);
  }

  const handleOfficeSelect = (event: React.ChangeEvent<any>) => {
    const office = event.target.value;
    updateOffice(office);
  };

  const renderChart = (chart: IBarChart | IHeatmapChart) => {
    switch (chart.type) {
      case "bar":
        return (
          <BarChart
            selectedOffice={state.selectedOffice}
            metric={chart.metric}
            dataMonthly={chart.dataMonthly}
            dataByRange={chart.dataByRange}
          ></BarChart>
        );
      case "heatmap":
        return (
          <HeatmapChart
            selectedOffice={state.selectedOffice}
            metrics={chart.metrics}
            data={chart.data}
          ></HeatmapChart>
        );
    }
  };

  return (
    <Layout>
      <Grid className={classes.header}>
        <Container maxWidth="md" className={classes.headerContainer}>
          <Typography variant="h1" className={classes.title}>
            {i18next.t("Reporting Dashboard")}
          </Typography>
          <FormControl>
            <Select
              className={classes.headerSelect}
              disableUnderline
              value={state.selectedOffice}
              onChange={handleOfficeSelect}
              inputProps={{
                name: "office",
                id: "office-select",
              }}
              MenuProps={{ classes: { paper: classes.dropdownStyle } }}
            >
              {offices.map((office) => (
                <MenuItem key={office} value={office}>
                  {office}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Container>
      </Grid>
      <Grid className={classes.pageHeader}>
        <Container maxWidth="md">
          <Box className={classes.iconAndTitle}>
            <BarChartIcon color="primary" />
            <Typography className={classes.secondTitle}>
              {i18next.t(state.selectedOffice)}
            </Typography>
          </Box>
        </Container>
      </Grid>
      <Container maxWidth="md">
        <Grid container spacing={3}>
          {state.charts.map((chart, i) => (
            <Grid key={i} item sm={12} md={6} className={classes.dataGrid}>
              {renderChart(chart)}
            </Grid>
          ))}
        </Grid>
      </Container>
    </Layout>
  );
}
