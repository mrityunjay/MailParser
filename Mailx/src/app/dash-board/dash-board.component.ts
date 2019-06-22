import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-dash-board',
  templateUrl: './dash-board.component.html',
  styleUrls: ['./dash-board.component.css']
})
export class DashBoardComponent implements OnInit {
public showorderlabels:boolean;
public paymentlabels:boolean;
public showpurchaselabels:boolean;
public emailData:any;
  constructor() {
    this.showorderlabels = false;
    this.showpurchaselabels = false;
    this.paymentlabels = false;
    this.emailData = ['order','Payment','Purchase']
   }
   listClicked(item){
     if(item=='order'){
      this.showorderlabels = true;
      this.showpurchaselabels = false;
      this.paymentlabels = false;
     }
     if(item=='Payment'){
      this.showorderlabels = false;
      this.showpurchaselabels = false;
      this.paymentlabels = true;
     }
     if(item=='Purchase'){
      this.showorderlabels = false;
      this.showpurchaselabels = true;
      this.paymentlabels = false;
     }
   }

  ngOnInit() {
  }

}
